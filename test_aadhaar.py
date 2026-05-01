"""
Test the extract_key_info patterns against sample Aadhaar card text.
This simulates what Tesseract would produce from the sample Aadhaar image.
"""
import sys
sys.path.insert(0, ".")
import document_analysis

# This is the approximate text Tesseract would extract from the sample Aadhaar card
SAMPLE_AADHAAR_TEXT = """
Unique Identification Authority of India
Government of India

Enrolment No.: 1118/00006/XXXXX

To : JoeGoaUk
s/o PioGoaUk
H. No. 12XX
Tarir,
Agassaim
North Goa
Goa - 403204
Mobile : 988XXXXXXXX

Ref. No : 00002335-00137106-xxxxxxxx -Goa-Panaji

UB 06722XXXX IN

Your Aadhaar No. :
5911 3340 XXXX

GOVERNMENT OF INDIA
JoeGoaUk
Year of Birth : 1947
Male

5911 3340 XXXX

Address: s/o PioGoaUk, House No. 12XX, Tarir, Agassaim, Goa-Panaji,
North Goa, Goa, 403204
"""

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
