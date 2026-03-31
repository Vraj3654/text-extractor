import sys
import os
sys.path.append('c:\\Users\\DEVI\\Downloads\\Text_Extractor-main\\Text_Extractor-main')
import document_analysis
import json

text = """GOVERNMENT OF INDIA
AADHAAR
Name: Ramesh Kumar
DOB: 15/08/1990
Gender: Male

Address:
Flat 402, Sunshine Apartments,
MG Road, Bangalore,
Karnataka 560001
"""

info = document_analysis.extract_key_info(text)
print(json.dumps(info, indent=2))
