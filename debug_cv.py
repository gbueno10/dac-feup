import cv2
import numpy as np
import sys
import os

# Add current dir to path to import cv_utils
sys.path.append(os.getcwd())
from cv_utils import detect_a4, extract_object_contour

def debug_image(image_path):
    print(f"Analyzing {image_path}...")
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to load image")
        return

    # 1. A4 Detection Debug
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    cv2.imwrite("debug_1_edged.jpg", edged)
    print("Saved debug_1_edged.jpg")

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    
    debug_cnts = image.copy()
    cv2.drawContours(debug_cnts, cnts, -1, (0, 0, 255), 2)
    cv2.imwrite("debug_2_contours.jpg", debug_cnts)
    print("Saved debug_2_contours.jpg")

    warped, scale, paper_contour = detect_a4(image)
    
    if warped is None:
        print("A4 Detection FAILED")
        return
    else:
        print(f"A4 Detected. Scale: {scale}")
        cv2.imwrite("debug_3_warped.jpg", warped)

    # 2. Object Detection Debug
    # Try with default params
    contour_points = extract_object_contour(warped, scale)
    
    # Visualize thresholding used in extract_object_contour
    gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray_warped, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    cv2.imwrite("debug_4_thresh.jpg", thresh)
    print("Saved debug_4_thresh.jpg")
    
    if contour_points:
        print(f"Object Contour Found: {len(contour_points)} points")
    else:
        print("Object Contour NOT Found")

if __name__ == "__main__":
    img_path = "/Users/gbuenos/.gemini/antigravity/brain/1300988b-61ab-468d-955b-a1fe5021c808/uploaded_image_1764427082358.png"
    debug_image(img_path)
