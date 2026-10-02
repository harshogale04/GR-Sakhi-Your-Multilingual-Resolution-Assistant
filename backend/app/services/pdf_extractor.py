"""
Robust PDF Extraction Pipeline for Maharashtra Government Resolutions.
Supports:
- Digital text extraction via PyPDF / pdfplumber.
- Tesseract OCR fallback (mar+hin+eng) for scanned Devanagari pages.
- Gemini multimodal PDF extraction for complex layouts and visual document understanding.
- Section heading detection (Marathi, Hindi, English).
- Extraction quality checks (detects empty / sparse text, preserves warnings, avoids false success).
"""
import io
import re
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import pytesseract
    import pdfplumber
    HAS_LOCAL_OCR = True
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
except Exception as e:
    logger.warning(f"Local OCR (pytesseract/pdfplumber) initialization notice: {e}")
    HAS_LOCAL_OCR = False

# Section headings commonly found in Maharashtra Government Resolutions
SECTION_PATTERNS = [
    # Marathi Headings — use Unicode-safe lookahead instead of \b (only works for ASCII)
    (re.compile(r"^\s*(?:१\.|I\.|[\*\-])?\s*(शासन\s+निर्णय|शासकीय\s+निर्णय|GOVERNMENT\s+RESOLUTION)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "शासन निर्णय / Resolution"),
    (re.compile(r"^\s*(?:२\.|II\.|[\*\-])?\s*(प्रस्तावना|PREAMBLE|BACKGROUND)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "प्रस्तावना / Preamble"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(पात्रतेचे\s+निकष|पात्रता|ELIGIBILITY\s+CRITERIA|ELIGIBILITY)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "पात्रता / Eligibility"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(अटी\s+व\s+शर्ती|नियम\s+व\s+अटी|TERMS\s+AND\s+CONDITIONS)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "अटी व शर्ती / Terms"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(कार्यपद्धती|अंमलबजावणी|PROCEDURE|IMPLEMENTATION)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "कार्यपद्धती / Procedure"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(वित्तीय\s+तरतूद|आर्थिक\s+तरतूद|FINANCIAL\s+IMPLICATION|BUDGET)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "वित्तीय तरतूद / Financial"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(परिशिष्ट\s*[-–—]?\s*[अ-हA-Z0-9]*|ANNEXURE|APPENDIX)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "परिशिष्ट / Annexure"),
    (re.compile(r"^\s*(?:[\d\.\*\-]*)\s*(आदेश|ORDER|CIRCULAR|परिपत्रक)(?=[\s:।|,\-]|$)", re.IGNORECASE | re.MULTILINE), "आदेश / Order"),
]

class PDFExtractionResult:
    def __init__(
        self,
        pages: List[Dict[str, Any]],
        total_pages: int,
        warnings: List[str],
        has_text: bool,
        primary_method: str,
    ):
        self.pages = pages  # [{"page_number": int, "text": str, "method": str, "section": str, "quality": float}]
        self.total_pages = total_pages
        self.warnings = warnings
        self.has_text = has_text
        self.primary_method = primary_method

    @property
    def full_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.pages if p.get("text"))


class PDFExtractor:
    @staticmethod
    def detect_section_heading(text: str) -> Optional[str]:
        """Detects section heading at the start of a passage."""
        for pattern, section_name in SECTION_PATTERNS:
            if pattern.search(text[:500]):
                return section_name
        return None

    @classmethod
    def extract(cls, pdf_bytes: bytes, max_multimodal_pages: int = 5) -> PDFExtractionResult:
        """
        Extracts document text page by page with quality checks and fallback tiers:
        Tier 1: Native digital PDF extraction (PyPDF / pdfplumber).
        Tier 2: Tesseract OCR for scanned/low-char pages (mar+hin+eng).
        Tier 3: Gemini Multimodal PDF processing for complex visual layouts (page-limited).
        """
        warnings: List[str] = []
        pages: List[Dict[str, Any]] = []

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            total_pages = len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to open PDF stream: {e}")
            return PDFExtractionResult(
                pages=[],
                total_pages=0,
                warnings=[f"Invalid or corrupted PDF file: {str(e)}"],
                has_text=False,
                primary_method="failed",
            )

        if total_pages == 0:
            return PDFExtractionResult(
                pages=[],
                total_pages=0,
                warnings=["PDF contains zero pages."],
                has_text=False,
                primary_method="empty",
            )

        current_active_section = "प्रस्तावना / Introduction"
        methods_used: Dict[str, int] = {}

        for i, page in enumerate(reader.pages):
            page_num = i + 1
            extracted_text = ""
            method = "pypdf"

            # 1. Native PyPDF extraction
            try:
                native_text = (page.extract_text() or "").strip()
                extracted_text = native_text
            except Exception as e:
                logger.debug(f"PyPDF failed on page {page_num}: {e}")
                extracted_text = ""

            # 2. Check quality: if character count is suspiciously low (< 50 chars), trigger OCR
            if len(extracted_text) < 50:
                logger.info(f"Page {page_num} has sparse text ({len(extracted_text)} chars). Triggering OCR fallback...")
                ocr_text = cls._run_ocr_on_page(pdf_bytes, page_num)
                if ocr_text and len(ocr_text.strip()) > len(extracted_text):
                    extracted_text = ocr_text.strip()
                    method = "tesseract_ocr"
                    warnings.append(f"Page {page_num}: Extracted via Tesseract OCR (scanned Devanagari text).")
                else:
                    # 3. Gemini Multimodal fallback if OCR unavailable or low quality
                    if page_num <= max_multimodal_pages and settings.GEMINI_API_KEY:
                        mm_text = cls._extract_with_gemini_multimodal(pdf_bytes, page_num)
                        if mm_text and len(mm_text.strip()) > len(extracted_text):
                            extracted_text = mm_text.strip()
                            method = "gemini_multimodal"
                            warnings.append(f"Page {page_num}: Processed via Gemini Multimodal OCR.")

            # Record method
            methods_used[method] = methods_used.get(method, 0) + 1

            # Quality assessment
            if not extracted_text:
                warnings.append(f"Page {page_num}: No readable text could be extracted.")
                quality_score = 0.0
            elif len(extracted_text) < 80:
                warnings.append(f"Page {page_num}: Low text volume extracted ({len(extracted_text)} chars).")
                quality_score = 0.4
            else:
                quality_score = 1.0

            # Detect section heading on page
            detected_sec = cls.detect_section_heading(extracted_text)
            if detected_sec:
                current_active_section = detected_sec

            pages.append({
                "page_number": page_num,
                "text": extracted_text,
                "method": method,
                "section": current_active_section,
                "quality": quality_score,
            })

        # Quality check across document
        total_text_chars = sum(len(p["text"]) for p in pages)
        has_text = total_text_chars > 30

        if not has_text:
            warnings.append("Document extraction failed: No readable text found across any pages.")

        primary_method = max(methods_used.items(), key=lambda x: x[1])[0] if methods_used else "none"

        return PDFExtractionResult(
            pages=pages,
            total_pages=total_pages,
            warnings=warnings,
            has_text=has_text,
            primary_method=primary_method,
        )

    @classmethod
    def _run_ocr_on_page(cls, pdf_bytes: bytes, page_number: int) -> str:
        """Runs Tesseract OCR on a specific page using Marathi + Hindi + English language models."""
        if not HAS_LOCAL_OCR:
            return ""

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                if page_number <= len(pdf.pages):
                    page = pdf.pages[page_number - 1]
                    # Render page at 200 DPI for Devanagari ligature accuracy
                    img = page.to_image(resolution=200).original
                    # Try Marathi + Hindi + English first
                    try:
                        return pytesseract.image_to_string(img, lang="mar+hin+eng")
                    except Exception:
                        try:
                            return pytesseract.image_to_string(img, lang="mar+eng")
                        except Exception:
                            return pytesseract.image_to_string(img)
        except Exception as e:
            logger.debug(f"Tesseract OCR failed on page {page_number}: {e}")
        return ""

    @classmethod
    def _extract_with_gemini_multimodal(cls, pdf_bytes: bytes, page_number: int) -> str:
        """
        Uses Gemini Flash multimodal understanding on a single page rendering.
        Never sends arbitrarily large multi-page PDFs to respect rate and token limits.
        """
        if not settings.GEMINI_API_KEY:
            return ""

        try:
            import google.generativeai as genai
            from PIL import Image

            if HAS_LOCAL_OCR:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    if page_number <= len(pdf.pages):
                        page = pdf.pages[page_number - 1]
                        pil_img = page.to_image(resolution=150).original
                        img_byte_arr = io.BytesIO()
                        pil_img.save(img_byte_arr, format="PNG")
                        img_bytes = img_byte_arr.getvalue()

                        model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
                        prompt = (
                            "Extract all text exactly as written from this official Maharashtra Government Resolution document. "
                            "Preserve original Marathi Devanagari script, Marathi headings, GR numbers, and table layouts accurately. "
                            "Do not summarize. Return verbatim text only."
                        )
                        response = model.generate_content([
                            prompt,
                            {"mime_type": "image/png", "data": img_bytes}
                        ])
                        if response and response.text:
                            return response.text
        except Exception as e:
            logger.debug(f"Gemini multimodal extraction on page {page_number} failed: {e}")
        return ""
