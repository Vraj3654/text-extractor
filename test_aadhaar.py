"""
Test the extract_key_info patterns against sample Aadhaar card text.
This simulates what Tesseract would produce from the sample Aadhaar image.
"""
import sys
sys.path.insert(0, ".")
import document_analysis

with open("test_aadhaar.txt", "r") as f:
    SAMPLE_AADHAAR_TEXT = f.read()

print("=" * 60)
print("TESTING EXTRACT_KEY_INFO AGAINST AADHAAR SAMPLE TEXT")
print("=" * 60)

result = document_analysis.extract_key_info(SAMPLE_AADHAAR_TEXT)

print("\nFORM FILL FIELDS:")
for k, v in result.get("form_fill", {}).items():
    status = "OK" if v else "EMPTY"
    print(f"  {k}: '{v}' [{status}]")

print("\nALL EXTRACTED INFO:")
for k, v in result.items():
    if k != "form_fill":
        print(f"  {k}: {v}")

print("\n" + "=" * 60)
print("CLASSIFICATION:")
classification = document_analysis.classify_document(SAMPLE_AADHAAR_TEXT)
print(f"  Type: {classification['type']} ({classification['confidence']}%)")
