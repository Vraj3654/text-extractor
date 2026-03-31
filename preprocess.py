import cv2
import os
import numpy as np

def deskew(image):
    # Invert image to get text coordinates
    gray = cv2.bitwise_not(image)
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    if abs(angle) < 0.5:
        return image
        
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess_image(image_bytes):
    # 1. Load Image from bytes into numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Provided bytes could not be decoded into an image.")
    
    # 2. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Enhance Contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # 4. Remove Noise (Light Blur)
    blur = cv2.GaussianBlur(enhanced, (5, 5), 0)

    # 5. ADAPTIVE THRESHOLDING
    thresh = cv2.adaptiveThreshold(
        blur, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 
        2
    )

    # 6. Deskew the thresholded image
    deskewed = deskew(thresh)

    # 7. Dilation/Erosion (Optional Cleanup)
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.erode(deskewed, kernel, iterations=1) 

    return processed

if __name__ == "__main__":
    # Test run
    try:
        preprocess_image("images/input.jpg", "output/processed.png", show_preview=True)
    except Exception as e:
        print(f"Error: {e}")