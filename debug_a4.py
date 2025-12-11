import cv2
import numpy as np
import sys
import os

def debug_a4_strategies(image_path):
    print(f"Analyzing {image_path}...")
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to load image")
        return

    # Resize for consistent processing (keep aspect ratio)
    height, width = image.shape[:2]
    max_dim = 1000
    scale = max_dim / max(height, width)
    new_width = int(width * scale)
    new_height = int(height * scale)
    resized = cv2.resize(image, (new_width, new_height))
    
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Strategy A: Canny Edge Detection
    edged = cv2.Canny(blurred, 75, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edged, kernel, iterations=2) # More dilation
    cv2.imwrite("debug_a4_canny.jpg", dilated)

    # Strategy B: Adaptive Thresholding (often better for paper)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    # Invert if needed (we want white paper to be white, background black? 
    # Actually findContours looks for white object on black background)
    # Usually paper is brighter than desk.
    # Let's try Otsu's thresholding too
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite("debug_a4_otsu.jpg", otsu)
    
    # Find contours on Canny (Strategy A)
    cnts_a, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts_a = sorted(cnts_a, key=cv2.contourArea, reverse=True)[:5]
    
    vis_a = resized.copy()
    cv2.drawContours(vis_a, cnts_a, -1, (0, 0, 255), 2)
    cv2.imwrite("debug_a4_contours_canny.jpg", vis_a)

    # Find contours on Otsu (Strategy B)
    cnts_b, _ = cv2.findContours(otsu.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts_b = sorted(cnts_b, key=cv2.contourArea, reverse=True)[:5]
    
    vis_b = resized.copy()
    cv2.drawContours(vis_b, cnts_b, -1, (0, 255, 0), 2)
    cv2.imwrite("debug_a4_contours_otsu.jpg", vis_b)

    print("Generated debug images.")

if __name__ == "__main__":
    img_path = "/Users/gbuenos/.gemini/antigravity/brain/1300988b-61ab-468d-955b-a1fe5021c808/uploaded_image_1764427082358.png"
    debug_a4_strategies(img_path)
