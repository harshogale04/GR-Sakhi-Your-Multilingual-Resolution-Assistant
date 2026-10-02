"""
Metadata Extractor for Maharashtra Government Resolutions (शासन निर्णय).
Extracts: Department, GR Number, Subject (विषय), Category, Document Type, Language, Page Count.
Strictly adheres to existing Supabase `documents` columns only.
Does NOT overwrite user-supplied metadata with uncertain extracted values.
"""
import re
from typing import Dict, Any, Optional
from backend.app.core.logging import logger

# Recognized Maharashtra Government Departments in Marathi & English
MAHARASHTRA_DEPARTMENTS = {
    # Marathi department names
    "शालेय शिक्षण": "School Education",
    "शालेय शिक्षण व क्रीडा": "School Education",
    "उच्च व तंत्र शिक्षण": "Higher Education",
    "वित्त": "Finance",
    "कृषी": "Agriculture",
    "कृषी, पशुसंवर्धन": "Agriculture",
    "सार्वजनिक आरोग्य": "Public Health",
    "महसूल व वन": "Revenue & Forest",
    "ग्राम विकास": "Rural Development",
    "नगर विकास": "Urban Development",
    "गृह विभाग": "Home Department",
    "उद्योग, ऊर्जा": "Industry & Energy",
    "महिला व बाल विकास": "Women & Child Development",
    "सामाजिक न्याय": "Social Justice",
    "पाणी पुरवठा": "Water Supply",
    "सामान्य प्रशासन": "General Administration",
    # English equivalents
    "school education": "School Education",
    "higher and technical education": "Higher Education",
    "finance": "Finance",
    "agriculture": "Agriculture",
    "public health": "Public Health",
    "revenue and forest": "Revenue & Forest",
    "rural development": "Rural Development",
    "urban development": "Urban Development",
    "home department": "Home Department",
    "general administration": "General Administration",
}

# Regex patterns for Maharashtra GR Numbers
# Examples:
# संकीर्ण-२०२४/प्र.क्र.४५/का.१२
# वैशिअ-२०२३/प्र.क्र.१०२/सेवा-२
# GR No. BUD-2024/CR-12/SER-1
GR_NUMBER_PATTERNS = [
    re.compile(r"शासन\s+निर्णय\s+क्रमांक\s*[:ः\-]?\s*([A-Za-z\u0900-\u097F0-9\-\.\/]+(?:/[A-Za-z\u0900-\u097F0-9\-\.]+)*)", re.IGNORECASE),
    re.compile(r"क्रमांक\s*[:ः\-]?\s*([A-Za-z\u0900-\u097F0-9\-\.\/]+(?:/[A-Za-z\u0900-\u097F0-9\-\.]+)*)", re.IGNORECASE),
    re.compile(r"GR\s*(?:No\.?|Number)\s*[:\-]?\s*([A-Za-z0-9\-\.\/]+)", re.IGNORECASE),
    re.compile(r"([A-Za-z\u0900-\u097F]{2,15}-\d{4}/(?:प्र\.क्र\.|CR|\d+)/[A-Za-z0-9\u0900-\u097F\-\.]+)", re.IGNORECASE),
]

# Patterns for Subject (विषय)
SUBJECT_PATTERNS = [
    re.compile(r"विषय\s*[:ः\-]\s*([^\n\r]+(?:\n[^\n\r]+){0,2})", re.MULTILINE),
    re.compile(r"Subject\s*[:\-]\s*([^\n\r]+(?:\n[^\n\r]+){0,2})", re.IGNORECASE | re.MULTILINE),
]


class MetadataExtractor:
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detects primary language: Marathi ('mr'), Hindi ('hi'), or English ('en').
        Distinguishes Marathi from Hindi using Marathi-specific grammatical markers.
        """
        if not text or not text.strip():
            return "mr"

        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        latin_chars = len(re.findall(r"[A-Za-z]", text))

        if latin_chars > devanagari_chars * 1.5:
            return "en"

        # Check for Marathi-specific vocabulary and morphological suffixes
        marathi_markers = [
            r"\bआहे\b", r"\bनाही\b", r"\bकेले\b", r"\bकरण्यात\b", r"\bशासन\b",
            r"\bनिर्णय\b", r"\bपरिपत्रक\b", r"\bत्यानुसार\b", r"\bतसेच\b",
            r"\bयांच्या\b", r"\bअधिकृत\b", r"\bमहाराष्ट्र\b", r"\bपात्रता\b",
            r"च्या", r"साठी", r"कडून", r"नुसार", r"मधील",
        ]
        marathi_score = sum(len(re.findall(m, text)) for m in marathi_markers)

        hindi_markers = [
            r"\bहै\b", r"\bहैं\b", r"\bकिया\b", r"\bगया\b", r"\bहोगा\b",
            r"\bसरकार\b", r"\bआदेश\b", r"\bनियम\b", r"\bके\s+लिए\b",
            r"\bद्वारा\b", r"\bइस\b", r"\bउस\b",
        ]
        hindi_score = sum(len(re.findall(h, text)) for h in hindi_markers)

        if marathi_score >= hindi_score:
            return "mr"
        return "hi"

    @staticmethod
    def extract_department(text: str) -> Optional[str]:
        """Detects Maharashtra Government department from text."""
        lower_text = text.lower()
        for pattern_str, standard_name in MAHARASHTRA_DEPARTMENTS.items():
            if pattern_str.lower() in lower_text:
                return standard_name
        return None

    @staticmethod
    def extract_gr_number(text: str) -> Optional[str]:
        """Extracts official GR number from resolution header text."""
        header_text = text[:3000]  # GR numbers always appear in the first few pages/header
        for pattern in GR_NUMBER_PATTERNS:
            match = pattern.search(header_text)
            if match:
                gr_num = match.group(1).strip().strip(".,:; ")
                if len(gr_num) >= 5 and any(char.isdigit() for char in gr_num):
                    return gr_num
        return None

    @staticmethod
    def extract_subject(text: str) -> Optional[str]:
        """Extracts Subject / विषय from resolution header."""
        header_text = text[:4000]
        for pattern in SUBJECT_PATTERNS:
            match = pattern.search(header_text)
            if match:
                raw_subject = match.group(1).strip()
                # Clean up newlines and excessive spaces
                cleaned = " ".join(raw_subject.split())
                if 5 <= len(cleaned) <= 300:
                    return cleaned
        return None

    @staticmethod
    def extract_category(text: str) -> str:
        """Determines category based on resolution keywords."""
        t = text.lower()
        if any(w in t for w in ["योजना", "अनुदान", "सबसिडी", "सहाय्य", "scheme", "subsidy", "grant"]):
            return "Scheme"
        if any(w in t for w in ["धोरण", "नियमावली", "मार्गदर्शक", "policy", "guidelines"]):
            return "Policy"
        if any(w in t for w in ["भरती", "निवड", "पदभरती", "recruitment", "vacancy", "appointment"]):
            return "Recruitment"
        if any(w in t for w in ["बदली", "पदोन्नती", "नियुक्ती", "transfer", "promotion"]):
            return "Transfer"
        if any(w in t for w in ["आर्थिक", "वित्तीय", "बजेट", "तरतूद", "financial", "budget", "expenditure"]):
            return "Financial"
        if any(w in t for w in ["परिपत्रक", "circular"]):
            return "Circular"
        return "Policy"

    @staticmethod
    def extract_document_type(text: str) -> str:
        """Detects whether document is a GR, Circular, Notification, or Order."""
        t = text.lower()
        if "शासन परिपत्रक" in t or "circular" in t:
            return "Circular"
        if "राजपत्र" in t or "gazette" in t or "अधिसूचना" in t or "notification" in t:
            return "Official Gazette"
        if "शासन आदेश" in t or "order" in t:
            return "Order"
        return "Government Resolution"

    @classmethod
    def enrich_document_metadata(
        cls,
        document_text: str,
        user_supplied: Dict[str, Any],
        page_count: int,
    ) -> Dict[str, Any]:
        """
        Enriches document metadata strictly within existing `documents` schema columns.
        Does NOT overwrite user-supplied metadata.
        """
        extracted_dept = cls.extract_department(document_text)
        extracted_gr = cls.extract_gr_number(document_text)
        extracted_subject = cls.extract_subject(document_text)
        detected_lang = cls.detect_language(document_text)
        extracted_cat = cls.extract_category(document_text)
        extracted_doc_type = cls.extract_document_type(document_text)

        # Merge, giving precedence to user-supplied non-empty values
        final_dept = user_supplied.get("department") or extracted_dept
        final_gr = user_supplied.get("gr_number") or extracted_gr
        final_subject = user_supplied.get("subject") or extracted_subject or user_supplied.get("original_filename")
        final_cat = user_supplied.get("category") or extracted_cat
        final_doc_type = user_supplied.get("document_type") or extracted_doc_type
        final_lang = user_supplied.get("language") or detected_lang

        return {
            "department": final_dept,
            "gr_number": final_gr,
            "subject": final_subject,
            "category": final_cat,
            "document_type": final_doc_type,
            "language": final_lang,
            "pages": page_count,
        }
