"""
image_pipeline.py — Unified Image Preprocessing Pipelines

Three distinct pipelines for different input types:

  1. process_scanned_document(bytes)
       → For Upload & OCR tab: PDFs, flat scans, typewritten docs
       → Uses aggressive adaptive thresholding + deskew

  2. process_id_document(bytes)
       → For Smart Form tab: Aadhaar, PAN, Passport, Driving License
       → Uses gentle denoise + unsharp mask (preserves color card detail)

  3. process_camera_snapshot(bytes, handwriting=False)
       → For Live Camera tab: phone snapshots
       → Printed mode: sharpen + CLAHE
       → Handwriting mode: Otsu binarisation + dilation
"""

import cv2
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _decode(image_bytes: bytes) -> np.ndarray:
    """Decode raw bytes into an OpenCV BGR image array."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes into an image.")
    return img


def _scale_down(img: np.ndarray, max_width: int = 2000) -> np.ndarray:
    """Scale image down if wider than max_width (preserves aspect ratio)."""
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)
    return img


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Correct rotation angle using minAreaRect on white pixels."""
    inverted = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(inverted > 0))
    if len(coords) == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:
        return gray
    h, w = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE 1 — SCANNED DOCUMENTS  (Upload & OCR tab)
# ─────────────────────────────────────────────────────────────────────────────

def process_scanned_document(image_bytes: bytes) -> np.ndarray:
    """
    Heavy preprocessing for flat scanned documents:
    invoices, receipts, certificates, letters, academic reports, etc.

    Steps: grayscale → CLAHE → Gaussian blur → adaptive threshold → deskew → erode
    Best for: PNG/TIFF scans, typewritten or printed text on white paper.
    """
    img = _decode(image_bytes)

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 3. Remove noise
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

    # 4. Adaptive binarisation — ideal for uneven lighting on flat docs
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # 5. Deskew
    deskewed = _deskew(thresh)

    # 6. Light erosion to remove specks
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.erode(deskewed, kernel, iterations=1)

    return processed


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE 2 — IDENTITY / GOVERNMENT DOCUMENTS  (Smart Form tab)
# ─────────────────────────────────────────────────────────────────────────────

def process_id_document(image_bytes: bytes) -> np.ndarray:
    """
    Gentle preprocessing for photos of identity & government documents:
    Aadhaar, PAN card, Passport, Driving License, Voter ID, etc.

    Key differences from scanned docs:
    - Cards are already small & colorful — aggressive thresholding destroys them
    - OCR works better on lightly processed grayscale than harsh B&W binarisation
    - Scale down phone camera's high-res shots before processing

    Steps: scale → grayscale → denoise → unsharp mask → CLAHE
    """
    img = _decode(image_bytes)

    # 1. Scale down large phone photos (4K → max 2000px wide)
    img = _scale_down(img, max_width=2000)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Gentle denoising (h=10 is conservative — preserves fine print)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 4. Unsharp mask — sharpens character edges without blowing out background
    blurred = cv2.GaussianBlur(denoised, (0, 0), 3)
    sharpened = cv2.addWeighted(denoised, 1.5, blurred, -0.5, 0)

    # 5. Light CLAHE for contrast (clipLimit=1.5 is gentle)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    result = clahe.apply(sharpened)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE 3 — CAMERA SNAPSHOTS  (Live Camera tab)
# ─────────────────────────────────────────────────────────────────────────────

def process_camera_snapshot(image_bytes: bytes, handwriting: bool = False) -> np.ndarray:
    """
    Preprocessing for manual snapshots taken from a webcam or phone camera.

    Two sub-modes:
    - Printed text (default): gentle sharpen + CLAHE, PSM 3 is best
    - Handwriting mode: Otsu binarisation + dilation, PSM 11 is best

    Args:
        image_bytes: Raw JPEG bytes from canvas.toDataURL()
        handwriting: If True, uses the handwriting-optimised pipeline
    """
    img = _decode(image_bytes)
    img = _scale_down(img, max_width=2000)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if handwriting:
        # ── Handwriting sub-pipeline ───────────────────────────────────────
        # Otsu automatically finds the best ink/paper threshold
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Dilate to thicken thin pen/pencil strokes
        kernel = np.ones((2, 2), np.uint8)
        return cv2.dilate(thresh, kernel, iterations=1)

    else:
        # ── Printed text sub-pipeline ──────────────────────────────────────
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        blurred = cv2.GaussianBlur(denoised, (0, 0), 3)
        sharpened = cv2.addWeighted(denoised, 1.5, blurred, -0.5, 0)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        return clahe.apply(sharpened)
