import pytesseract
from PIL import Image
import re
import os

from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

# =========================
# TESSERACT CONFIGURATION
# =========================

# Windows default path for Tesseract
WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def configure_tesseract(tesseract_cmd=None):
    if tesseract_cmd is None:
        # Auto-detect: check Windows default install path first
        if os.path.exists(WINDOWS_TESSERACT_PATH):
            tesseract_cmd = WINDOWS_TESSERACT_PATH
        else:
            # Fallback: assume it's on system PATH
            tesseract_cmd = "tesseract"
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    print(f"[Tesseract] Using: {tesseract_cmd}")


# =========================
# LOAD AI MODEL (LAZY, OPTIONAL)
# =========================

MODEL_NAME = "vennify/t5-base-grammar-correction"
_tokenizer = None
_model = None
_ai_available = False

def _load_ai_model():
    global _tokenizer, _model, _ai_available
    if _ai_available:
        return True
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        _ai_available = True
        print("[AI] Grammar correction model loaded successfully.")
    except Exception as e:
        print(f"[AI] Model unavailable (will skip AI correction): {e}")
        _ai_available = False
    return _ai_available


# =========================
# POST-OCR FIXES (SAFE)
# =========================

def fix_ocr_artifacts(text):
    """
    Fix OCR mechanical errors (rule-based, safe)
    """
    text = text.replace('£', '₹')
    text = re.sub(r'(\d+)°', r'\1th', text)
    text = re.sub(r'(?<=[a-z])[|!](?=[a-z])', 'l', text)
    text = re.sub(r'(?<=[A-Z])[|!](?=[A-Z])', 'I', text)
    return text


# =========================
# AI TEXT CORRECTION
# =========================

def ai_text_correction(text):
    """
    Applies transformer-based grammar & spelling correction.
    Falls back gracefully if AI model is unavailable.
    """
    if not _load_ai_model():
        # Fallback: return text as-is (OCR artifacts already fixed)
        return text

    corrected_lines = []

    for line in text.split('\n'):
        if not line.strip():
            corrected_lines.append(line)
            continue

        # Skip lines with lots of digits (IDs, dates, amounts)
        digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
        if digit_ratio > 0.25:
            corrected_lines.append(line)
            continue

        try:
            input_text = "grammar: " + line
            input_ids = _tokenizer.encode(input_text, return_tensors="pt", truncation=True)
            outputs = _model.generate(
                input_ids,
                max_length=128,
                num_beams=4,
                early_stopping=True
            )
            corrected_line = _tokenizer.decode(outputs[0], skip_special_tokens=True)
            corrected_lines.append(corrected_line)
        except Exception:
            corrected_lines.append(line)

    return "\n".join(corrected_lines)


# =========================
# DOCUMENT-SPECIFIC FIXES
# =========================

def document_specific_fix(text):
    text = text.replace('Principat', 'Principal')
    return text


# =========================
# MAIN OCR FUNCTION
# =========================

def extract_text_from_image(cv2_image_array, languages='eng'):
    
    custom_config = r'--oem 3 --psm 4 -c preserve_interword_spaces=1'
    
    # Convert cv2 numpy array to PIL Image compatible with pytesseract
    img = Image.fromarray(cv2_image_array)

    # Step 1: OCR
    raw_text = pytesseract.image_to_string(img, config=custom_config, lang=languages)

    # Step 2: Extract Confidence
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config, lang=languages)
    confidences = [int(c) for c in data['conf'] if str(c) != '-1']
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    # Step 3: Detect Language
    detected_lang = "unknown"
    if raw_text.strip():
        try:
            detected_lang = detect(raw_text)
        except:
            pass

    # Step 4: OCR artifact fixes
    text = fix_ocr_artifacts(raw_text)

    # Step 5: AI correction (graceful fallback if torch not working)
    text = ai_text_correction(text)

    # Step 6: Document-specific cleanup
    final_text = document_specific_fix(text)

    return {
        "raw_text": raw_text, 
        "corrected_text": final_text,
        "confidence": round(avg_conf, 2),
        "detected_language": detected_lang
    }


# =========================
# TEST BLOCK
# =========================

if __name__ == "__main__":
    try:
        configure_tesseract()
        print("AI-powered OCR pipeline ready.")
    except Exception as e:
        print(f"Error: {e}")
