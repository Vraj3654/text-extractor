"""
Document Analysis Module
Handles: Classification, Key Info Extraction, Translation
"""

import re
from typing import Dict, Any, List

# ===========================
# DOCUMENT CLASSIFICATION
# ===========================

DOCUMENT_TYPES = {
    "Invoice": {
        "keywords": ["invoice", "bill", "total amount", "amount due", "payment", "subtotal", "tax", "gst",
                     "invoice no", "invoice number", "due date", "bill to", "sold to", "item", "qty", "quantity"],
        "icon": "🧾"
    },
    "Receipt": {
        "keywords": ["receipt", "thank you for your purchase", "cash", "change", "cashier",
                     "store", "shop", "purchased", "transaction", "order", "paid"],
        "icon": "🛒"
    },
    "Certificate": {
        "keywords": ["certificate", "certify", "awarded", "achievement", "completion", "hereby",
                     "authorized", "accredited", "diploma", "degree", "congratulations"],
        "icon": "🏆"
    },
    "Identity Document": {
        "keywords": ["date of birth", "dob", "gender", "nationality", "passport", "id card",
                     "aadhar", "driving license", "pan card", "voter id", "expiry", "address"],
        "icon": "🪪"
    },
    "Medical Report": {
        "keywords": ["diagnosis", "patient", "doctor", "hospital", "prescription", "medicine",
                     "dosage", "symptoms", "treatment", "laboratory", "test results", "blood",
                     "report", "clinical", "physician"],
        "icon": "🏥"
    },
    "Legal Document": {
        "keywords": ["agreement", "contract", "terms and conditions", "hereby agrees", "parties",
                     "clause", "pursuant", "jurisdiction", "litigation", "plaintiff", "defendant",
                     "whereas", "witnesseth", "notary", "affidavit", "deed"],
        "icon": "⚖️"
    },
    "Academic": {
        "keywords": ["student", "marks", "grade", "examination", "school", "college", "university",
                     "subject", "semester", "result", "pass", "fail", "cgpa", "gpa", "roll number"],
        "icon": "🎓"
    },
    "Business Letter": {
        "keywords": ["dear", "sincerely", "regards", "yours faithfully", "to whom it may concern",
                     "subject:", "reference:", "kindly", "enclosed", "attached"],
        "icon": "📄"
    },
    "Bank Statement": {
        "keywords": ["account number", "ifsc", "balance", "debit", "credit", "transaction",
                     "statement", "bank", "withdraw", "deposit", "account holder", "branch"],
        "icon": "🏦"
    },
}

def classify_document(text: str) -> Dict[str, Any]:
    """Classify document type based on keyword matching."""
    if not text or not text.strip():
        return {"type": "Unknown", "icon": "📃", "confidence": 0, "scores": {}}

    text_lower = text.lower()
    scores = {}

    for doc_type, config in DOCUMENT_TYPES.items():
        matched = sum(1 for kw in config["keywords"] if kw in text_lower)
        if matched > 0:
            confidence = min((matched / 3) * 100, 100.0)
            scores[doc_type] = round(confidence, 1)

    if not scores:
        return {"type": "General Document", "icon": "📃", "confidence": 0, "scores": {}}

    best_type = max(scores, key=scores.get)
    return {
        "type": best_type,
        "icon": DOCUMENT_TYPES[best_type]["icon"],
        "confidence": scores[best_type],
        "scores": scores
    }


# ===========================
# KEY INFO EXTRACTION
# ===========================

def extract_key_info(text: str) -> Dict[str, Any]:
    """Extract structured key information from OCR text using regex."""
    info = {}

    # ── Dates (multiple formats) ──────────────────────────────────────────────
    date_patterns = [
        r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b',
    ]
    dates = []
    for pat in date_patterns:
        dates += re.findall(pat, text, re.IGNORECASE)
    if dates:
        info["dates"] = list(dict.fromkeys(dates))[:5]

    # ── Email ─────────────────────────────────────────────────────────────────
    emails = re.findall(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text)
    if emails:
        info["emails"] = list(dict.fromkeys(emails))[:5]

    # ── Phone numbers ─────────────────────────────────────────────────────────
    phones = re.findall(
        r'(?:\+?91[\s\-]?)?(?:[6-9]\d{9}|(?:\(?0\d{2,4}\)?[\s\-]?)?\d{6,8})', text)
    phones = [p.strip() for p in phones if len(re.sub(r'\D', '', p)) >= 7]
    if phones:
        info["phone_numbers"] = list(dict.fromkeys(phones))[:5]

    # ── Money / Amounts ───────────────────────────────────────────────────────
    amounts = re.findall(
        r'(?:₹|Rs\.?|INR|USD|\$|€|£)\s*[\d,]+(?:\.\d{1,2})?|[\d,]+(?:\.\d{1,2})?\s*(?:₹|Rs\.?|INR)',
        text, re.IGNORECASE)
    if amounts:
        info["amounts"] = list(dict.fromkeys(amounts))[:5]

    # ── PAN Number ───────────────────────────────────────────────────────────
    pan = re.findall(r'\b[A-Z]{5}\d{4}[A-Z]\b', text)
    if pan:
        info["pan_numbers"] = list(dict.fromkeys(pan))

    # ── Aadhaar Number (12 digits, possibly spaced in groups of 4) ───────────
    aadhaar = re.findall(r'\b\d{4}\s?\d{4}\s?\d{4}\b', text)
    if aadhaar:
        info["aadhaar_numbers"] = list(dict.fromkeys(aadhaar))[:2]

    # ── Percentages ───────────────────────────────────────────────────────────
    percentages = re.findall(r'\b\d+(?:\.\d+)?%', text)
    if percentages:
        info["percentages"] = list(dict.fromkeys(percentages))[:5]

    # ── URLs ──────────────────────────────────────────────────────────────────
    urls = re.findall(r'(?:https?://|www\.)[^\s<>"\']+', text, re.IGNORECASE)
    if urls:
        info["urls"] = list(dict.fromkeys(urls))[:3]

    # =========================================================================
    # SMART FORM AUTO-FILL (Aadhaar-aware)
    # =========================================================================
    form_fill = {"name": "", "dob": "", "address": "", "gender": ""}

    # ── Name ─────────────────────────────────────────────────────────────────
    # Pattern 1: explicit "Name :" or "To :" label (Aadhaar front says "To : <Name>")
    name_from_label = re.search(
        r'\b(?:Name|Customer|Client|To|Student|Employee|Holder|Recipient)\s*[:\-]\s*([a-zA-Z][a-zA-Z\s\.]{1,40})',
        text, re.IGNORECASE)
    # Pattern 2: "Government of India" block followed by a standalone name line
    name_after_gov = re.search(
        r'Government of India\s+([a-zA-Z][a-zA-Z\s\.]{2,40})\s*\n', text, re.IGNORECASE)
    if name_from_label:
        form_fill["name"] = name_from_label.group(1).strip().split('\n')[0]
    elif name_after_gov:
        form_fill["name"] = name_after_gov.group(1).strip()

    # ── Date of Birth ─────────────────────────────────────────────────────────
    # Pattern 1: explicit DOB / Date of Birth keyword with date
    specific_dob = re.search(
        r'\b(?:DOB|Date of Birth|Birth Date)\b\s*[:\-]?\s*'
        r'((?:[0-3]?\d[\/\-\.][0-1]?\d[\/\-\.]\d{2,4})|(?:[0-3]?\d\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}))',
        text, re.IGNORECASE)
    # Pattern 2: "Year of Birth : 1947" (Aadhaar-specific)
    yob = re.search(r'\b(?:Year of Birth|YOB)\s*[:\-]?\s*(\d{4})\b', text, re.IGNORECASE)

    if specific_dob:
        form_fill["dob"] = specific_dob.group(1).strip()
    elif yob:
        form_fill["dob"] = yob.group(1).strip()
    elif dates:
        form_fill["dob"] = dates[0]

    # Pattern 3: Name fallback - Line immediately above DOB if Name wasn't found
    if not form_fill["name"] and form_fill["dob"]:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if form_fill["dob"] in line and i > 0:
                possible_name = lines[i-1].strip()
                # Clean up if the previous line had "Name:" but OCR garbled the keyword
                possible_name = re.sub(r'^(?i)(?:Name|Nane|Nam)[:\-\s]*', '', possible_name).strip()
                if possible_name and len(possible_name) > 2 and not re.search(r'\d', possible_name):
                    form_fill["name"] = possible_name
                    break

    # ── Gender ────────────────────────────────────────────────────────────────
    gender_match = re.search(r'\b(?:Gender|Sex)\b\s*[:\-]?\s*(Male|Female|Transgender|M|F)\b', text, re.IGNORECASE)
    if gender_match:
        form_fill["gender"] = gender_match.group(1).capitalize()
    else:
        implicit_g = re.search(r'\b(Male|Female)\b', text, re.IGNORECASE)
        if implicit_g:
            form_fill["gender"] = implicit_g.group(1).capitalize()

    # ── Address ───────────────────────────────────────────────────────────────
    # Pattern 1: explicit "Address :" keyword block
    address_match = re.search(
        r'\b(?:Address|Add|Address[:])\s*[:\-]?\s*([A-Za-z0-9\s\,\.\-\/\n]{10,200}?(?:\b\d{3}\s?\d{3}\b))',
        text, re.IGNORECASE | re.DOTALL)
    # Pattern 2: "s/o ... <city> <state> <pin>" which is Aadhaar format
    aadhaar_address = re.search(
        r's[\/\\]o\s+[A-Za-z\s\.]+,?\s+([A-Za-z0-9\s\,\.\-]+\d{3}\s?\d{3})',
        text, re.IGNORECASE)
    if address_match:
        form_fill["address"] = re.sub(r'\s+', ' ', address_match.group(1)).strip()
    elif aadhaar_address:
        form_fill["address"] = re.sub(r'\s+', ' ', aadhaar_address.group(0)).strip()
    else:
        # Fallback: Capture up to 150 chars before a PIN code
        pin_match = re.search(r'([A-Za-z0-9\s\,\.\-\/]{20,150}?\b\d{3}\s?\d{3}\b)', text)
        if pin_match:
            form_fill["address"] = re.sub(r'\s+', ' ', pin_match.group(1)).strip()

    # ── Phone from form ───────────────────────────────────────────────────────
    mob = re.search(r'(?:Mobile|Mob|Ph|Phone)\s*[:\-]?\s*(\+?[\d\s\-]{8,15})', text, re.IGNORECASE)
    if mob:
        info.setdefault("phone_numbers", [])
        mob_clean = re.sub(r'\D', '', mob.group(1))
        if mob_clean not in [re.sub(r'\D', '', p) for p in info["phone_numbers"]]:
            info["phone_numbers"].append(mob.group(1).strip())

    info["form_fill"] = form_fill
    return info


# ===========================
# TRANSLATION
# ===========================

SUPPORTED_LANGUAGES = {
    "Hindi": "hi",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Italian": "it",
    "Tamil": "ta",
    "Telugu": "te",
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Urdu": "ur",
    "English": "en",
}

def translate_text(text: str, target_lang_code: str) -> Dict[str, Any]:
    """Translate text using deep-translator (Google Translate backend)."""
    if not text or not text.strip():
        return {"success": False, "error": "No text to translate", "translated": ""}

    try:
        from deep_translator import GoogleTranslator
        # Limit to 4500 chars to avoid API limits
        chunk = text[:4500]
        translated = GoogleTranslator(source='auto', target=target_lang_code).translate(chunk)
        truncated = len(text) > 4500
        return {
            "success": True,
            "translated": translated,
            "target_language": target_lang_code,
            "truncated": truncated,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "translated": "",
            "target_language": target_lang_code,
            "truncated": False
        }
