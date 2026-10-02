"""
Section-Aware, Page-Preserving Chunking Service for Maharashtra Government Resolutions.
Splits text along Devanagari sentence delimiters (danda '।', newlines, periods)
to avoid truncating critical provisions, conditions, or financial figures.
Retains strict page-level provenance and stable chunk IDs.
"""
import re
from typing import List, Dict, Any, Optional
from uuid import UUID


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: UUID,
        text: str,
        page: int,
        section: str,
        language: str,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.page = page
        self.section = section
        self.language = language
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": str(self.document_id),
            "text": self.text,
            "page": self.page,
            "section": self.section,
            "language": self.language,
            "metadata": self.metadata,
        }


class ChunkingService:
    DEFAULT_CHUNK_SIZE = 800     # characters (~120-150 Marathi words)
    DEFAULT_CHUNK_OVERLAP = 150  # characters (~20-25 words)

    # Delimiters in priority order: paragraphs -> Devanagari danda / periods -> lines -> spaces
    SENTENCE_SPLIT_REGEX = re.compile(r"([।\n\r\.\?!]+)")

    @classmethod
    def split_into_sentences(cls, text: str) -> List[str]:
        """Splits Devanagari or English text into complete sentences/provisions."""
        raw_parts = cls.SENTENCE_SPLIT_REGEX.split(text)
        sentences: List[str] = []
        current = ""

        for part in raw_parts:
            current += part
            if cls.SENTENCE_SPLIT_REGEX.match(part):
                cleaned = current.strip()
                if cleaned:
                    sentences.append(cleaned)
                current = ""

        if current.strip():
            sentences.append(current.strip())

        return sentences

    @classmethod
    def chunk_pages(
        cls,
        document_id: UUID,
        pages: List[Dict[str, Any]],
        document_metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        language: str = "mr",
    ) -> List[DocumentChunk]:
        """
        Creates section-aware, page-preserving chunks.
        Guarantees that every chunk has a stable identifier:
        `{document_id}_p{page}_c{index}`
        """
        doc_meta = document_metadata or {}
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 1

        for p in pages:
            page_num = p.get("page_number", 1)
            page_text = (p.get("text") or "").strip()
            page_section = p.get("section") or "सामान्य / General"

            if not page_text:
                continue

            sentences = cls.split_into_sentences(page_text)
            if not sentences:
                continue

            current_chunk_sentences: List[str] = []
            current_len = 0

            for sentence in sentences:
                sent_len = len(sentence)

                # If single sentence is larger than chunk_size, split by word window
                if sent_len > chunk_size:
                    if current_chunk_sentences:
                        chunk_text = " ".join(current_chunk_sentences).strip()
                        c_id = f"{document_id}_p{page_num}_c{global_chunk_idx}"
                        chunks.append(
                            DocumentChunk(
                                chunk_id=c_id,
                                document_id=document_id,
                                text=chunk_text,
                                page=page_num,
                                section=page_section,
                                language=language,
                                metadata={
                                    "filename": doc_meta.get("filename", ""),
                                    "original_filename": doc_meta.get("original_filename", ""),
                                    "gr_number": doc_meta.get("gr_number", ""),
                                    "department": doc_meta.get("department", ""),
                                    "subject": doc_meta.get("subject", ""),
                                },
                            )
                        )
                        global_chunk_idx += 1
                        current_chunk_sentences = []
                        current_len = 0

                    # Sub-split long sentence by words
                    words = sentence.split()
                    word_pos = 0
                    while word_pos < len(words):
                        sub_words = words[word_pos:word_pos + 120]
                        sub_text = " ".join(sub_words)
                        c_id = f"{document_id}_p{page_num}_c{global_chunk_idx}"
                        chunks.append(
                            DocumentChunk(
                                chunk_id=c_id,
                                document_id=document_id,
                                text=sub_text,
                                page=page_num,
                                section=page_section,
                                language=language,
                                metadata={
                                    "filename": doc_meta.get("filename", ""),
                                    "original_filename": doc_meta.get("original_filename", ""),
                                    "gr_number": doc_meta.get("gr_number", ""),
                                    "department": doc_meta.get("department", ""),
                                    "subject": doc_meta.get("subject", ""),
                                },
                            )
                        )
                        global_chunk_idx += 1
                        word_pos += 90  # overlap ~30 words
                    continue

                if current_len + sent_len > chunk_size and current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences).strip()
                    c_id = f"{document_id}_p{page_num}_c{global_chunk_idx}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=c_id,
                            document_id=document_id,
                            text=chunk_text,
                            page=page_num,
                            section=page_section,
                            language=language,
                            metadata={
                                "filename": doc_meta.get("filename", ""),
                                "original_filename": doc_meta.get("original_filename", ""),
                                "gr_number": doc_meta.get("gr_number", ""),
                                "department": doc_meta.get("department", ""),
                                "subject": doc_meta.get("subject", ""),
                            },
                        )
                    )
                    global_chunk_idx += 1

                    # Retain last sentence for overlap
                    overlap_sentences = []
                    overlap_len = 0
                    for s in reversed(current_chunk_sentences):
                        if overlap_len + len(s) <= chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_len += len(s)
                        else:
                            break
                    current_chunk_sentences = overlap_sentences
                    current_len = overlap_len

                current_chunk_sentences.append(sentence)
                current_len += sent_len

            # Flush remaining sentences for the page
            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences).strip()
                c_id = f"{document_id}_p{page_num}_c{global_chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=c_id,
                        document_id=document_id,
                        text=chunk_text,
                        page=page_num,
                        section=page_section,
                        language=language,
                        metadata={
                            "filename": doc_meta.get("filename", ""),
                            "original_filename": doc_meta.get("original_filename", ""),
                            "gr_number": doc_meta.get("gr_number", ""),
                            "department": doc_meta.get("department", ""),
                            "subject": doc_meta.get("subject", ""),
                        },
                    )
                )
                global_chunk_idx += 1

        return chunks
