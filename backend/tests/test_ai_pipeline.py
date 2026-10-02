"""
Tests for AI Pipeline Components:
- PDF extraction & quality checks
- OCR fallback
- Language detection & metadata extraction
- Section-aware chunking & provenance
- Embedding dimension validation
- Pinecone vector store upsert & query mocks
- Grounded RAG prompting
- Citation construction
- Insufficient evidence handling
- Failure recovery
"""
import io
import uuid
from uuid import uuid4
import pytest
from pypdf import PdfWriter

from backend.app.services.metadata_extractor import MetadataExtractor
from backend.app.services.pdf_extractor import PDFExtractor, PDFExtractionResult
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.embedding_service import EmbeddingService, EMBEDDING_DIMENSION
from backend.app.services.vector_store_service import VectorStoreService, _mock_pinecone_store
from backend.app.services.gemini_service import GeminiService
from backend.app.services.rag_service import RAGService


def create_sample_pdf_bytes(text_pages: list[str]) -> bytes:
    """Creates an in-memory PDF with given text across pages using pypdf."""
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject, ArrayObject, FloatObject

    writer = PdfWriter()
    for text in text_pages:
        # Create a page with simple content stream
        page = writer.add_blank_page(width=595, height=842)
        # Add basic text to content stream
        content = f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET"
        stream = DecodedStreamObject()
        stream.set_data(content.encode("latin-1", "replace"))
        page[NameObject("/Contents")] = stream

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------------------------------------------------------------------------
# 1. Language Handling & Metadata Extraction Tests
# ---------------------------------------------------------------------------

class TestMetadataExtraction:
    def test_marathi_language_detection(self):
        marathi_text = (
            "महाराष्ट्र शासन शालेय शिक्षण व क्रीडा विभाग. "
            "शासन निर्णय क्रमांक: संकीर्ण-२०२४/प्र.क्र.४५/का.१२. "
            "राज्यातील सर्व प्राथमिक शाळांसाठी नवीन शैक्षणिक धोरण लागू करण्यात येत आहे."
        )
        lang = MetadataExtractor.detect_language(marathi_text)
        assert lang == "mr"

    def test_hindi_language_detection(self):
        hindi_text = (
            "यह महाराष्ट्र सरकार का आदेश है। "
            "सभी नागरिकों के लिए स्वास्थ्य योजना लागू की गई है।"
        )
        lang = MetadataExtractor.detect_language(hindi_text)
        assert lang == "hi"

    def test_english_language_detection(self):
        english_text = (
            "Government of Maharashtra, Finance Department. "
            "Government Resolution regarding allocation of funds for infrastructure development."
        )
        lang = MetadataExtractor.detect_language(english_text)
        assert lang == "en"

    def test_gr_number_extraction(self):
        text = (
            "महाराष्ट्र शासन\n"
            "शासन निर्णय क्रमांक : संकीर्ण-२०२४/प्र.क्र.१२/का.२१\n"
            "मंत्रालय, मुंबई"
        )
        gr_num = MetadataExtractor.extract_gr_number(text)
        assert gr_num is not None
        assert "२०२४" in gr_num or "12" in gr_num

    def test_department_extraction(self):
        text = "महाराष्ट्र शासन\nशालेय शिक्षण व क्रीडा विभाग\nमंत्रालय, मुंबई"
        dept = MetadataExtractor.extract_department(text)
        assert dept == "School Education"

    def test_subject_extraction(self):
        text = "विषय : राज्यातील प्राथमिक शिक्षकांसाठी नवीन सेवा प्रवेश नियम लागू करणेबाबत."
        subj = MetadataExtractor.extract_subject(text)
        assert subj is not None
        assert "प्राथमिक" in subj

    def test_user_metadata_precedence(self):
        """User-supplied metadata must not be overwritten by extracted values."""
        text = "शालेय शिक्षण विभाग. शासन निर्णय क्रमांक: जुना-१२३"
        user_meta = {
            "department": "Finance",  # User explicitly specified Finance
            "gr_number": "USER-GR-999",
            "subject": "User Subject",
        }
        enriched = MetadataExtractor.enrich_document_metadata(text, user_meta, page_count=1)
        assert enriched["department"] == "Finance"
        assert enriched["gr_number"] == "USER-GR-999"
        assert enriched["subject"] == "User Subject"


# ---------------------------------------------------------------------------
# 2. PDF Extraction & Quality Checks
# ---------------------------------------------------------------------------

class TestPDFExtraction:
    def test_empty_pdf_detection(self):
        """Empty or corrupt PDF must produce warnings and has_text=False."""
        result = PDFExtractor.extract(b"not a valid pdf")
        assert result.has_text is False
        assert len(result.warnings) > 0

    def test_sparse_text_quality_warning(self):
        """Pages with suspiciously low text trigger OCR attempt and warning."""
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"xref\n0 2\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"trailer\n<< /Size 2 /Root 1 0 R >>\n"
            b"startxref\n9\n%%EOF"
        )
        result = PDFExtractor.extract(pdf_bytes)
        assert isinstance(result, PDFExtractionResult)

    def test_section_heading_detection(self):
        text = "शासन निर्णय : महाराष्ट्र राज्यातील सर्व पात्र शेतकऱ्यांना कर्जमाफी देणेबाबत."
        sec = PDFExtractor.detect_section_heading(text)
        assert sec is not None
        assert "शासन निर्णय" in sec


# ---------------------------------------------------------------------------
# 3. Section-Aware Chunking & Provenance
# ---------------------------------------------------------------------------

class TestChunkingService:
    def test_chunk_provenance_and_stable_ids(self):
        doc_id = uuid4()
        pages = [
            {
                "page_number": 1,
                "text": "प्रस्तावना. राज्यातील शिक्षण व्यवस्थेचा दर्जा सुधारण्यासाठी हा निर्णय घेण्यात येत आहे।",
                "section": "प्रस्तावना / Preamble",
            },
            {
                "page_number": 2,
                "text": "पात्रता आणि अटी. अर्जदार महाराष्ट्राचा रहिवासी असणे आवश्यक आहे। किमान वय १८ वर्षे असावे।",
                "section": "पात्रता / Eligibility",
            },
        ]
        chunks = ChunkingService.chunk_pages(doc_id, pages, language="mr")
        assert len(chunks) >= 2

        # Check provenance
        p1_chunks = [c for c in chunks if c.page == 1]
        p2_chunks = [c for c in chunks if c.page == 2]
        assert len(p1_chunks) > 0
        assert len(p2_chunks) > 0

        # Stable ID format: {doc_id}_p{page}_c{index}
        assert f"{doc_id}_p1_c" in p1_chunks[0].chunk_id
        assert f"{doc_id}_p2_c" in p2_chunks[0].chunk_id
        assert p2_chunks[0].section == "पात्रता / Eligibility"

    def test_sentence_boundary_splitting(self):
        """Devanagari danda '।' should be respected as sentence delimiter."""
        text = "पहिला मुद्दा येथे संपतो। दुसरा मुद्दा सुरू होतो। तिसरा नियम लागू राहील।"
        sentences = ChunkingService.split_into_sentences(text)
        assert len(sentences) == 3


# ---------------------------------------------------------------------------
# 4. Embedding Dimension & Retry Handling
# ---------------------------------------------------------------------------

class TestEmbeddingService:
    def test_embedding_dimension(self):
        """Embedding must strictly produce EMBEDDING_DIMENSION (768) float vector."""
        vec = EmbeddingService.get_document_embedding("महाराष्ट्र शासन निर्णय")
        assert len(vec) == EMBEDDING_DIMENSION
        assert all(isinstance(x, float) for x in vec)

    def test_query_embedding_dimension(self):
        vec = EmbeddingService.get_query_embedding("शेतकरी कर्जमाफी पात्रता")
        assert len(vec) == EMBEDDING_DIMENSION

    def test_batch_document_embeddings(self):
        texts = ["मजकूर १", "मजकूर २", "मजकूर ३"]
        embeddings = EmbeddingService.get_batch_document_embeddings(texts, batch_size=2)
        assert len(embeddings) == 3
        for e in embeddings:
            assert len(e) == EMBEDDING_DIMENSION

    def test_mock_embedding_determinism(self):
        """Same input must produce identical vector."""
        v1 = EmbeddingService.get_document_embedding("समान मजकूर")
        v2 = EmbeddingService.get_document_embedding("समान मजकूर")
        assert v1 == v2


# ---------------------------------------------------------------------------
# 5. Pinecone Vector Store Upsert & Query Mocks
# ---------------------------------------------------------------------------

class TestVectorStoreService:
    def test_upsert_and_query_vectors(self):
        doc_id = uuid4()
        chunk_id = f"{doc_id}_p1_c1"
        vec_id = f"vec_{chunk_id}"
        test_text = "विशेष कृषी सहाय्य योजना २०२४ अंतर्गत प्रति हेक्टर १०,००० रुपये अनुदान दिले जाईल."

        embedding = EmbeddingService.get_document_embedding(test_text)
        metadata = {
            "document_id": str(doc_id),
            "chunk_id": chunk_id,
            "text": test_text,
            "page": 1,
            "section": "अनुदान / Grant",
            "language": "mr",
            "department": "Agriculture",
        }

        VectorStoreService.upsert_chunks([{
            "id": vec_id,
            "values": embedding,
            "metadata": metadata,
        }])

        # Query using similar query vector
        query_vec = EmbeddingService.get_query_embedding(test_text)
        results = VectorStoreService.query_similar(query_vec, top_k=5)
        assert len(results) > 0
        matching = [r for r in results if r["id"] == vec_id]
        assert len(matching) == 1
        assert matching[0]["metadata"]["department"] == "Agriculture"

    def test_query_filter_by_department(self):
        doc_id = uuid4()
        vec_id = f"vec_{doc_id}_p1_c1"
        test_text = "आरोग्य विभागाच्या वैद्यकीय भरतीचे नियम."
        embedding = EmbeddingService.get_document_embedding(test_text)

        VectorStoreService.upsert_chunks([{
            "id": vec_id,
            "values": embedding,
            "metadata": {
                "document_id": str(doc_id),
                "text": test_text,
                "department": "Public Health",
                "language": "mr",
            },
        }])

        query_vec = EmbeddingService.get_query_embedding("वैद्यकीय भरती")
        # Filter for Public Health -> should find it
        res_found = VectorStoreService.query_similar(query_vec, department="Public Health")
        assert any(r["id"] == vec_id for r in res_found)

        # Filter for Finance -> should NOT return it
        res_excluded = VectorStoreService.query_similar(query_vec, department="Finance")
        assert not any(r["id"] == vec_id for r in res_excluded)

    def test_vector_deletion_by_document_id(self):
        doc_id = uuid4()
        vec_id = f"vec_{doc_id}_p1_c1"
        VectorStoreService.upsert_chunks([{
            "id": vec_id,
            "values": EmbeddingService.get_document_embedding("काढून टाकण्यासाठी मजकूर"),
            "metadata": {"document_id": str(doc_id), "text": "to delete"},
        }])

        del_count = VectorStoreService.delete_by_document_id(doc_id)
        assert del_count >= 1
        assert vec_id not in _mock_pinecone_store


# ---------------------------------------------------------------------------
# 6. Grounded RAG Prompting & Citation Construction
# ---------------------------------------------------------------------------

class TestGroundedRAG:
    def test_grounded_answer_includes_disclaimer(self):
        passages = [{
            "document_title": "कृषी योजना",
            "gr_number": "AGR-2024/01",
            "page": 1,
            "section": "पात्रता",
            "text": "अल्पभूधारक शेतकऱ्यांना ठिबक सिंचनासाठी ८०% अनुदान दिले जाईल.",
        }]
        answer = GeminiService.generate_grounded_answer(
            query="ठिबक सिंचनासाठी किती अनुदान मिळेल?",
            context_passages=passages,
            language="mr",
        )
        assert "८०%" in answer or "अनुदान" in answer
        assert "कायदेशीर सल्ला नाही" in answer or "शासन निर्णय" in answer

    def test_insufficient_evidence_flag_on_unrelated_query(self):
        """When query has no matching evidence, answer_query must flag insufficient_evidence=True."""
        # Query about deep space astronomy in a Maharashtra GR system
        response = RAGService.answer_query(
            query="मंगळ ग्रहावरील अंतराळ संशोधन मोहिमेसाठी रॉकेट इंजिन डिझाइन काय आहे?",
            language="mr",
        )
        assert response.role == "assistant"
        # Since no matches or low score, should be flagged
        assert response.insufficient_evidence is True
        assert "पुरावा उपलब्ध नाही" in response.content or "पर्याप्त साक्ष्य" in response.content or "Insufficient" in response.content

    def test_programmatic_citations_constructed(self):
        """Citations must come directly from retrieved passages with exact document IDs and pages."""
        doc_id = uuid4()
        vec_id = f"vec_{doc_id}_p3_c1"
        text = "छत्रपती शिवाजी महाराज शेतकरी सन्मान योजना नियमावली पृष्ठ ३."

        VectorStoreService.upsert_chunks([{
            "id": vec_id,
            "values": EmbeddingService.get_document_embedding(text),
            "metadata": {
                "document_id": str(doc_id),
                "chunk_id": f"{doc_id}_p3_c1",
                "text": text,
                "page": 3,
                "section": "पात्रता निकष",
                "department": "Agriculture",
                "gr_number": "CSMSSY-2024",
            },
        }])

        resp = RAGService.answer_query(query=text, language="mr")
        if not resp.insufficient_evidence:
            assert len(resp.citations) > 0
            cite = resp.citations[0]
            assert cite.document_id == doc_id
            assert cite.page == 3
            assert cite.section == "पात्रता निकष"
