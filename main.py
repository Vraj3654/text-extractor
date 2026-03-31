import os
import sys

# Import our custom modules
import preprocess
import extract_text

# --- CONFIGURATION ---
BASE_DIR = os.getcwd() # Current working directory
INPUT_IMAGE = os.path.join(BASE_DIR, "images", "input.jpg")
PROCESSED_IMAGE = os.path.join(BASE_DIR, "output", "processed.png")
OUTPUT_TEXT = os.path.join(BASE_DIR, "output", "result.txt")

# Tesseract Path (Update if valid path differs)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def main():
    print("🚀 Starting OCR Pipeline...\n")

    try:
        # Step 0: Check if input exists
        if not os.path.exists(INPUT_IMAGE):
            print(f"❌ Error: Input file missing at {INPUT_IMAGE}")
            return

        # Step 1: Setup Tesseract
        extract_text.configure_tesseract(TESSERACT_PATH)

        # Step 2: Preprocessing
        print(f"1️⃣  Processing image: {os.path.basename(INPUT_IMAGE)}...")
        preprocess.preprocess_image(
            input_path=INPUT_IMAGE, 
            output_path=PROCESSED_IMAGE,
            show_preview=False  # Set True to see the image window
        )

        # Step 3: OCR Extraction
        print(f"2️⃣  Extracting text...")
        text = extract_text.extract_text_from_image(
            image_path=PROCESSED_IMAGE, 
            output_txt_path=OUTPUT_TEXT
        )

        # Step 4: Final Output
        print("\n" + "="*30)
        print("       OCR RESULT PREVIEW       ")
        print("="*30)
        print(text[:500].strip()) # Show first 500 chars
        if len(text) > 500: print("\n... [Check file for full text]")
        print("="*30 + "\n")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")

if __name__ == "__main__":
    main()