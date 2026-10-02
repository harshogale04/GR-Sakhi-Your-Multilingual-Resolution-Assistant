import io
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import pytesseract
    from PIL import Image
    import pdfplumber
    HAS_OCR = True
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
except Exception as e:
    logger.warning(f"OCR libraries initialization notice: {e}")
    HAS_OCR = False


class OCRService:
    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text page by page from raw PDF bytes.
        Falls back to Tesseract OCR when native text extraction yields empty/low character counts
        (characteristic of scanned Maharashtra GR documents).
        Returns:
            List[Dict[str, Any]]: [{"page_number": int, "text": str, "method": str}]
        """
        pages_content: List[Dict[str, Any]] = []

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            total_pages = len(reader.pages)
            logger.info(f"Processing PDF with {total_pages} pages.")

            for i, page in enumerate(reader.pages):
                page_num = i + 1
                extracted_text = (page.extract_text() or "").strip()

                # If text is too short or empty, attempt OCR fallback
                if len(extracted_text) < 50 and HAS_OCR:
                    logger.info(f"Page {page_num} has sparse text ({len(extracted_text)} chars). Attempting OCR fallback...")
                    ocr_text = OCRService._run_tesseract_ocr(pdf_bytes, page_num)
                    if ocr_text and len(ocr_text.strip()) > len(extracted_text):
                        extracted_text = ocr_text.strip()
                        method = "ocr"
                    else:
                        method = "pypdf_sparse"
                else:
                    method = "native"

                if extracted_text:
                    pages_content.append({
                        "page_number": page_num,
                        "text": extracted_text,
                        "method": method,
                    })

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            # If PyPDF fails completely, try pdfplumber fallback
            if HAS_OCR:
                pages_content = OCRService._extract_with_pdfplumber(pdf_bytes)

        return pages_content

    @staticmethod
    def _run_tesseract_ocr(pdf_bytes: bytes, page_number: int) -> str:
        """Run OCR on a specific page image."""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                if page_number <= len(pdf.pages):
                    page = pdf.pages[page_number - 1]
                    pil_img = page.to_image(resolution=200).original
                    # Try Marathi + Hindi + English OCR if language packs exist, else fallback to standard
                    try:
                        text = pytesseract.image_to_string(pil_img, lang="mar+hin+eng")
                    except Exception:
                        text = pytesseract.image_to_string(pil_img)
                    return text
        except Exception as e:
            logger.debug(f"OCR fallback attempt on page {page_number} failed: {e}")
        return ""

    @staticmethod
    def _extract_with_pdfplumber(pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Fallback extractor using pdfplumber."""
        pages = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append({
                            "page_number": idx + 1,
                            "text": text.strip(),
                            "method": "pdfplumber",
                        })
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
        return pages

    @staticmethod
    def chunk_document_text(
        pages: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        Splits page texts into contextual chunks with page metadata.
        Returns:
            List[Dict[str, Any]]: [{"chunk_index": int, "page": int, "section": str, "text": str}]
        """
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 1

        for p in pages:
            page_num = p["page_number"]
            text = p["text"]

            # Simple sliding window chunker preserving words
            words = text.split()
            if not words:
                continue

            current_word_idx = 0
            words_per_chunk = max(50, chunk_size // 6)
            overlap_words = max(10, chunk_overlap // 6)

            while current_word_idx < len(words):
                end_idx = min(len(words), current_word_idx + words_per_chunk)
                chunk_words = words[current_word_idx:end_idx]
                chunk_text = " ".join(chunk_words)

                # Attempt to extract section or heading preview
                section_title = f"Page {page_num} Section"
                if len(chunk_words) > 4:
                    first_few = " ".join(chunk_words[:5])
                    if any(kw in first_few for kw in ["शासन निर्णय", "प्रस्तावना", "परिशिष्ट", "नियम", "मार्गदर्शक"]):
                        section_title = first_few

                chunks.append({
                    "chunk_index": chunk_idx,
                    "page": page_num,
                    "section": section_title,
                    "text": chunk_text,
                })
                chunk_idx += 1

                if end_idx >= len(words):
                    break
                current_word_idx += (words_per_chunk - overlap_words)

        return chunks
