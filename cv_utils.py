import cv2
import numpy as np
from scipy.interpolate import splprep, splev

def detect_a4(image):
    """
    Detects an A4 paper in the image and warps the perspective to a top-down view.
    Robust version: uses resizing, multiple edge detection strategies, and area filtering.
    Returns:
        warped: The warped top-down image.
        scale: Pixels per mm.
        paper_contour: The 4 points of the detected paper in the original image (for visualization).
    """
    # Resize for consistent processing
    original_height, original_width = image.shape[:2]
    target_height = 1000
    ratio = original_height / target_height
    
    # If image is smaller than target, don't resize up, just use as is
    if original_height > target_height:
        new_width = int(original_width / ratio)
        resized = cv2.resize(image, (new_width, target_height))
    else:
        resized = image.copy()
        ratio = 1.0

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # List of strategies to try
    strategies = []
    
    # Strategy 1: Canny + Dilation
    edged = cv2.Canny(blurred, 75, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edged, kernel, iterations=2)
    strategies.append(dilated)
    
    # Strategy 2: Otsu Thresholding (good for high contrast)
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    strategies.append(otsu)
    
    # Strategy 3: Adaptive Thresholding
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    strategies.append(adaptive)

    screenCnt = None
    best_area = 0
    
    for edge_map in strategies:
        cnts, _ = cv2.findContours(edge_map.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        for c in cnts:
            # Filter by area (must be at least 5% of image)
            area = cv2.contourArea(c)
            if area < (resized.shape[0] * resized.shape[1] * 0.05):
                continue
                
            peri = cv2.arcLength(c, True)
            # Try different approximations
            for eps in [0.02, 0.03, 0.04, 0.01, 0.05]:
                approx = cv2.approxPolyDP(c, eps * peri, True)
                if len(approx) == 4:
                    if area > best_area:
                        best_area = area
                        screenCnt = approx
                    break
            
            # If exact 4 corners not found, try minAreaRect for large contours
            if len(approx) != 4:
                 rect = cv2.minAreaRect(c)
                 box = cv2.boxPoints(rect)
                 box = np.int64(box)
                 if area > best_area:
                     best_area = area
                     screenCnt = box

    if screenCnt is None:
        return None, None, None

    # Scale points back to original image size
    screenCnt = screenCnt.astype("float32") * ratio
    screenCnt = screenCnt.astype("int")

    # Order points: top-left, top-right, bottom-right, bottom-left
    pts = screenCnt.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    (tl, tr, br, bl) = rect

    # Compute width and height of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # A4 size in mm
    a4_width_mm = 210
    a4_height_mm = 297

    # Destination points
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # Calculate scale (pixels per mm)
    if maxWidth < maxHeight:
        scale_x = maxWidth / a4_width_mm
        scale_y = maxHeight / a4_height_mm
    else:
        scale_x = maxWidth / a4_height_mm
        scale_y = maxHeight / a4_width_mm
    
    scale = (scale_x + scale_y) / 2
    return warped, scale, screenCnt

def extract_object_contour(image, scale, threshold_block_size=11, threshold_c=2):
    """
    Extracts the largest object contour from the warped A4 image.
    Returns the contour points in mm (centered at 0,0).
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Ensure block size is odd
    if threshold_block_size % 2 == 0:
        threshold_block_size += 1
        
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, threshold_block_size, threshold_c)
                                   
    # Morphological operations to remove noise (small dots) and close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Find contours
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not cnts:
        return None

    # Assume largest contour is the object
    c = max(cnts, key=cv2.contourArea)
    
    # Filter small contours (noise)
    if cv2.contourArea(c) < 100: # Arbitrary small area
        return None
    
    # Simplify contour
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.005 * peri, True) # 0.5% approximation

    # Convert to mm and center
    points_mm = []
    h, w = image.shape[:2]
    center_x, center_y = w / 2, h / 2

    for point in approx:
        px, py = point[0]
        # Center coordinates
        mm_x = (px - center_x) / scale
        mm_y = (center_y - py) / scale # Flip Y for OpenSCAD
        points_mm.append([mm_x, mm_y])

    return points_mm

def find_a4_at_point(image, point):
    """
    Finds the A4 paper contour that contains the given point (x, y).
    Returns: warped, scale, paper_contour
    """
    # Resize for consistent processing
    original_height, original_width = image.shape[:2]
    target_height = 1000
    ratio = original_height / target_height
    
    if original_height > target_height:
        new_width = int(original_width / ratio)
        resized = cv2.resize(image, (new_width, target_height))
        # Scale point to resized coordinates
        pt_x = int(point[0] / ratio)
        pt_y = int(point[1] / ratio)
    else:
        resized = image.copy()
        ratio = 1.0
        pt_x, pt_y = point

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use a combined edge map for better coverage
    edged = cv2.Canny(blurred, 75, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edged, kernel, iterations=2)
    
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    candidate_contours = []
    
    # From Canny
    cnts_canny, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidate_contours.extend(cnts_canny)
    
    # From Otsu
    cnts_otsu, _ = cv2.findContours(otsu.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidate_contours.extend(cnts_otsu)

    # Collect all containing contours
    containing_contours = []
    for c in candidate_contours:
        if cv2.pointPolygonTest(c, (pt_x, pt_y), False) >= 0:
            containing_contours.append(c)
            
    if not containing_contours:
        return None, None, None
        
    # Sort by area descending (largest first -> likely the A4 paper)
    containing_contours = sorted(containing_contours, key=cv2.contourArea, reverse=True)
    
    # Process the largest one
    c = containing_contours[0]
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    
    if len(approx) != 4:
         rect = cv2.minAreaRect(c)
         box = cv2.boxPoints(rect)
         approx = np.int64(box)
         
    screenCnt = approx

    # Scale points back
    screenCnt = screenCnt.astype("float32") * ratio
    screenCnt = screenCnt.astype("int")

    # Warp logic (copied from detect_a4)
    pts = screenCnt.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    a4_width_mm = 210
    a4_height_mm = 297
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    if maxWidth < maxHeight:
        scale_x = maxWidth / a4_width_mm
        scale_y = maxHeight / a4_height_mm
    else:
        scale_x = maxWidth / a4_height_mm
        scale_y = maxHeight / a4_width_mm
    scale = (scale_x + scale_y) / 2
    
    return warped, scale, screenCnt

def find_object_at_point(image, point, scale, thresh_block=11, thresh_c=2):
    """
    Finds the object contour in the warped image that contains the point.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if thresh_block % 2 == 0: thresh_block += 1
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, thresh_block, thresh_c)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    pt_x, pt_y = point
    
    # Find contour containing point
    found_cnt = None
    for c in cnts:
        if cv2.pointPolygonTest(c, (pt_x, pt_y), False) >= 0:
            found_cnt = c
            break
            
    if found_cnt is None:
        return None
        
    # Simplify and convert to mm
    peri = cv2.arcLength(found_cnt, True)
    approx = cv2.approxPolyDP(found_cnt, 0.005 * peri, True)
    
    points_mm = []
    h, w = image.shape[:2]
    center_x, center_y = w / 2, h / 2
    for p in approx:
        px, py = p[0]
        mm_x = (px - center_x) / scale
        mm_y = (center_y - py) / scale
        points_mm.append([mm_x, mm_y])
        
    return points_mm

def find_all_a4_candidates(image, min_area_ratio=0.1):
    """
    Find all potential A4 paper candidates in the image.
    Returns a list of contours that could be A4 paper.
    """
    # Resize for processing
    target_width = 800
    h_orig, w_orig = image.shape[:2]
    scale_factor = target_width / w_orig if w_orig > target_width else 1.0
    
    if scale_factor != 1.0:
        resized = cv2.resize(image, (target_width, int(h_orig * scale_factor)))
    else:
        resized = image.copy()
    
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Try multiple edge detection strategies
    candidates = []
    
    # Strategy 1: Canny
    edged = cv2.Canny(blurred, 50, 150)
    dilated = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by area
    image_area = resized.shape[0] * resized.shape[1]
    min_area = image_area * min_area_ratio
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            # Try to approximate to polygon
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            # Scale back to original size
            if scale_factor != 1.0:
                approx = (approx / scale_factor).astype(np.int32)
            
            candidates.append({
                'contour': approx,
                'area': area / (scale_factor ** 2),
                'corners': len(approx)
            })
    
    # Sort by area (largest first)
    candidates.sort(key=lambda x: x['area'], reverse=True)
    
    return candidates


def create_contour_overlay(image, candidates, alpha=0.3):
    """
    Create an overlay image with all candidate contours highlighted.
    """
    overlay = image.copy()
    
    # Generate distinct colors for each candidate
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
    ]
    
    for idx, candidate in enumerate(candidates[:6]):  # Limit to 6 for visibility
        color = colors[idx % len(colors)]
        
        # Fill the contour with semi-transparent color
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [candidate['contour']], -1, 255, -1)
        
        # Apply color to overlay
        colored = image.copy()
        colored[mask > 0] = color
        overlay = cv2.addWeighted(overlay, 1 - alpha, colored, alpha, 0)
        
        # Draw contour outline
        cv2.drawContours(overlay, [candidate['contour']], -1, color, 3)
    
    return overlay

def smooth_contour(points, s=1.0):
    """
    Smooths the contour using B-spline interpolation.
    """
    if len(points) < 4:
        return points
        
    points = np.array(points)
    x = points[:, 0]
    y = points[:, 1]
    
    # Close the loop
    x = np.append(x, x[0])
    y = np.append(y, y[0])

    tck, u = splprep([x, y], s=s, per=True)
    u_new = np.linspace(u.min(), u.max(), 100) # Resample with 100 points
    x_new, y_new = splev(u_new, tck, der=0)

    return list(zip(x_new, y_new))

def contour_to_openscad_points(points):
    """
    Formats points as an OpenSCAD polygon string.
    """
    points_str = ", ".join([f"[{x:.2f}, {y:.2f}]" for x, y in points])
    return f"[{points_str}]"


def find_all_object_candidates(image, min_area_ratio=0.01, max_objects=10, mask=None):
    """
    Find all potential objects in the warped A4 image.
    Returns a list of contours that could be objects.
    Enhanced with better filtering for solid objects.
    
    Args:
        image: Input image (warped A4)
        min_area_ratio: Minimum area as ratio of image size
        max_objects: Maximum number of objects to return
        mask: Optional binary mask (white = regions to detect, black = ignore)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    # Apply mask if provided
    if mask is not None:
        # Ensure mask is same size as image
        if mask.shape[:2] != gray.shape[:2]:
            mask = cv2.resize(mask, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_NEAREST)
        # Apply mask to blurred image
        blurred = cv2.bitwise_and(blurred, blurred, mask=mask)
    
    # Try multiple thresholding strategies
    all_contours = []
    
    # Strategy 1: Adaptive thresholding
    thresh_adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 15, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    thresh_adaptive = cv2.morphologyEx(thresh_adaptive, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh_adaptive = cv2.morphologyEx(thresh_adaptive, cv2.MORPH_OPEN, kernel)
    
    # Apply mask to threshold result
    if mask is not None:
        thresh_adaptive = cv2.bitwise_and(thresh_adaptive, thresh_adaptive, mask=mask)
    
    cnts_adaptive, _ = cv2.findContours(thresh_adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    all_contours.extend(cnts_adaptive)
    
    # Strategy 2: Otsu thresholding
    _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    thresh_otsu = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh_otsu = cv2.morphologyEx(thresh_otsu, cv2.MORPH_OPEN, kernel)
    
    # Apply mask to threshold result
    if mask is not None:
        thresh_otsu = cv2.bitwise_and(thresh_otsu, thresh_otsu, mask=mask)
    
    cnts_otsu, _ = cv2.findContours(thresh_otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    all_contours.extend(cnts_otsu)
    
    # Filter by area and quality metrics
    image_area = image.shape[0] * image.shape[1]
    min_area = image_area * min_area_ratio
    max_area = image_area * 0.7  # Don't include the entire image
    
    candidates = []
    seen_positions = []  # Track center positions to avoid duplicates
    
    for cnt in all_contours:
        area = cv2.contourArea(cnt)
        
        # Filter by area
        if area < min_area or area > max_area:
            continue
        
        # Calculate solidity (area / convex hull area)
        # Higher solidity = more solid object, less holes/noise
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        
        # Filter out very non-solid objects (likely noise or text)
        if solidity < 0.5:
            continue
        
        # Calculate extent (area / bounding box area)
        x, y, w, h = cv2.boundingRect(cnt)
        extent = area / (w * h)
        
        # Filter out very thin/elongated objects
        if extent < 0.3:
            continue
        
        # Calculate aspect ratio
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 100
        
        # Filter out extremely elongated objects (likely artifacts)
        if aspect_ratio > 5:
            continue
        
        # Check for duplicates by position
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w//2, y + h//2
        
        # Check if this is too close to an existing candidate
        is_duplicate = False
        for existing_cx, existing_cy, existing_area in seen_positions:
            distance = np.sqrt((cx - existing_cx)**2 + (cy - existing_cy)**2)
            area_ratio = min(area, existing_area) / max(area, existing_area)
            # If centers are close and areas similar, it's likely a duplicate
            if distance < 50 and area_ratio > 0.7:
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
        
        seen_positions.append((cx, cy, area))
        
        # Simplify contour
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.005 * peri, True)
        
        candidates.append({
            'contour': approx,
            'area': area,
            'corners': len(approx),
            'solidity': solidity,
            'extent': extent,
            'aspect_ratio': aspect_ratio,
            'center': (cx, cy)
        })
    
    # Sort by area (largest first) and limit results
    candidates.sort(key=lambda x: x['area'], reverse=True)
    
    return candidates[:max_objects]


def create_object_overlay(image, candidates, alpha=0.35):
    """
    Create an overlay image with all candidate object contours highlighted.
    Simple version without numbers for cleaner visualization.
    """
    overlay = image.copy()
    
    # Generate distinct colors for each candidate
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 255, 0),  # Light green
        (255, 128, 0),  # Orange
        (0, 128, 255),  # Light blue
        (255, 0, 128),  # Pink
    ]
    
    for idx, candidate in enumerate(candidates):
        color = colors[idx % len(colors)]
        
        # Fill the contour with semi-transparent color
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [candidate['contour']], -1, 255, -1)
        
        # Apply color to overlay
        colored = image.copy()
        colored[mask > 0] = color
        overlay = cv2.addWeighted(overlay, 1 - alpha, colored, alpha, 0)
        
        # Draw contour outline (thicker for better visibility)
        cv2.drawContours(overlay, [candidate['contour']], -1, color, 4)
    
    return overlay
