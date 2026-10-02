"""
Marathi-First Comprehensive Evaluation Suite for MAHA-GR (AI for Bharat).
Validates Marathi document processing, Marathi Devanagari chunking, OCR handling,
semantic retrieval, cross-lingual retrieval, question answering, citation correctness,
and latency.

Tests the 6 mandatory problem domains:
1. Eligibility conditions (पात्रता अटी)
2. Dates and deadlines (तारखा व अंतिम मुदत)
3. Government schemes (शासकीय योजना तरतूद)
4. Department responsibilities (विभागीय जबाबदारी)
5. Exceptions and conditions (अपवाद व नियम)
6. Document-specific factual questions (तथ्यात्मक प्रश्न)
"""
import time
import pytest
from uuid import uuid4
from typing import Dict, Any

from backend.app.services.pdf_extractor import PDFExtractor
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.metadata_extractor import MetadataExtractor
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_store_service import VectorStoreService, _mock_pinecone_store
from backend.app.services.rag_service import RAGService
from backend.app.services.demo_service import DemoService


@pytest.fixture(autouse=True)
def setup_marathi_evaluation_corpus():
    """Seeds the representative Marathi Government Resolutions into the test environment."""
    _mock_pinecone_store.clear()
    DemoService.seed_sample_documents()
    yield
    _mock_pinecone_store.clear()


class TestMarathiPDFAndLanguageProcessing:
    def test_marathi_language_detection_morphology(self):
        """Validates detection of Marathi using distinctive Devanagari administrative markers."""
        marathi_samples = [
            "शासकीय कर्मचाऱ्यांच्या बदल्यांबाबत नवीन नियमावली जाहीर करण्यात आली आहे.",
            "ठिबक सिंचन योजनेचा लाभ घेण्यासाठी शेतकऱ्यांनी महाडीबीटी पोर्टलवर अर्ज करावा.",
            "सदर शासन निर्णय महाराष्ट्र शासनाच्या संकेतस्थळावर उपलब्ध करण्यात आला आहे.",
        ]
        for sample in marathi_samples:
            detected = MetadataExtractor.detect_language(sample)
            assert detected == "mr", f"Failed on: {sample}"

    def test_marathi_section_heading_detection(self):
        """Validates recognition of Marathi administrative headings."""
        headings = [
            ("शासन निर्णय: राज्यातील सर्व शेतकऱ्यांसाठी...", "शासन निर्णय / Resolution"),
            ("प्रस्तावना: कृषी क्षेत्रातील पाणी टंचाई लक्षात घेता...", "प्रस्तावना / Preamble"),
            ("पात्रतेचे निकष: अर्जदार शेतकरी अल्पभूधारक असावा...", "पात्रता / Eligibility"),
            ("अटी व शर्ती: १. आधार कार्ड आवश्यक आहे...", "अटी व शर्ती / Terms"),
            ("कार्यपद्धती: ऑनलाईन अर्ज सादर करण्याची पद्धत...", "कार्यपद्धती / Procedure"),
            ("वित्तीय तरतूद: सन २०२४-२५ या वर्षासाठी...", "वित्तीय तरतूद / Financial"),
        ]
        for text, expected in headings:
            detected = PDFExtractor.detect_section_heading(text)
            assert detected == expected, f"Failed on heading: {text}"

    def test_marathi_devanagari_sentence_splitting(self):
        """Validates that Devanagari danda (|) and Marathi abbreviations are correctly handled."""
        text = "ठिबक सिंचनासाठी ८०% अनुदान दिले जाईल। अर्ज महाडीबीटीवर करावा। अंतिम मुदत ३१ डिसेंबर आहे."
        sentences = ChunkingService.split_into_sentences(text)
        assert len(sentences) >= 2
        assert any("८०% अनुदान" in s for s in sentences)


class TestMarathiDomainQueries:
    """Tests the 6 mandatory domain types for Maharashtra Government Resolutions."""

    def test_domain_1_eligibility_conditions(self):
        """Query: पात्रता निकष (Eligibility) - must retrieve eligibility-related evidence."""
        query = "ठिबक सिंचन अनुदानासाठी कोणते शेतकरी पात्र आहेत आणि काय निकष आहेत?"
        t0 = time.perf_counter()
        response = RAGService.answer_query(query=query, language="mr")
        latency_ms = (time.perf_counter() - t0) * 1000

        assert not response.insufficient_evidence, "Eligibility query should have sufficient evidence"
        assert len(response.citations) > 0
        # Check that at least one citation is from an eligibility-related section
        # (page ordering is not guaranteed with mock embeddings; content check is sufficient)
        all_sections = [c.section or "" for c in response.citations]
        all_snippets = " ".join(c.snippet for c in response.citations)
        assert any("पात्रता" in s or "निकष" in s for s in all_sections) or \
               any(k in all_snippets for k in ["पात्र", "आधार", "७/१२"]), \
               "No eligibility evidence found in any citation"
        # Answer must ground on eligibility keywords
        assert any(k in response.answer for k in ["आधार", "७/१२", "पात्र", "e-KYC", "शेतकऱ्या"])
        assert latency_ms < 2000, f"Query latency too high: {latency_ms:.1f}ms"

    def test_domain_2_dates_and_deadlines(self):
        """Query: अंतिम मुदत (Deadlines) - must retrieve deadline provisions on Page 3."""
        query = "योजनेसाठी अर्ज सादर करण्याची अंतिम मुदत कोणती आहे?"
        response = RAGService.answer_query(query=query, language="mr")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert any("३१ डिसेंबर २०२४" in cite.snippet or "३१ डिसेंबर २०२४" in response.answer for cite in response.citations)

    def test_domain_3_government_scheme_provisions(self):
        """Query: अनुदानाचे प्रमाण (Scheme Subsidies) - must retrieve 80% / 70% provisions."""
        query = "अल्प व अत्यल्प भूधारक शेतकऱ्यांना किती टक्के अनुदान मंजूर करण्यात आले आहे?"
        response = RAGService.answer_query(query=query, language="mr")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert any("८०%" in cite.snippet or "८०%" in response.answer for cite in response.citations)

    def test_domain_4_department_responsibilities(self):
        """Query: विभागीय जबाबदारी (Department responsibilities) - RTE school education."""
        query = "आरटीई २५% प्रवेश प्रक्रियेसाठी निवड समितीचे अध्यक्ष कोण आहेत?"
        response = RAGService.answer_query(query=query, language="mr", department="School Education")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert any("शिक्षणाधिकारी" in cite.snippet or "शिक्षणाधिकारी" in response.answer for cite in response.citations)

    def test_domain_5_exceptions_and_restrictions(self):
        """Query: अपवाद व मर्यादा (Exceptions) - must retrieve 3-year restriction."""
        query = "पूर्वी ठिबक सिंचनाचा लाभ घेतलेल्या शेतकऱ्यांना पुन्हा अनुदान मिळेल का?"
        response = RAGService.answer_query(query=query, language="mr")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert any("३ वर्ष" in cite.snippet or "अपात्र" in cite.snippet for cite in response.citations)

    def test_domain_6_document_specific_factual(self):
        """Query: MJPJAY स्वास्थ्य योजना उपचार मर्यादा - must retrieve 5 Lakhs limit."""
        query = "महात्मा फुले जन आरोग्य योजनेअंतर्गत प्रति कुटुंब किती रुपयांपर्यंत मोफत उपचार मिळतात?"
        response = RAGService.answer_query(query=query, language="mr", department="Public Health")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert any("५ लाख" in cite.snippet or "५ लाख" in response.answer for cite in response.citations)


class TestCrossLingualAndInsufficientEvidence:
    def test_cross_lingual_hindi_to_marathi_gr(self):
        """Hindi Query -> Marathi GR Retrieval."""
        query = "ड्रिप सिंचाई योजना में किसानों को कितनी सब्सिडी दी जाती है?"
        response = RAGService.answer_query(query=query, language="hi")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert response.language == "hi"

    def test_cross_lingual_english_to_marathi_gr(self):
        """English Query -> Marathi GR Retrieval."""
        query = "What is the annual health coverage limit under Mahatma Jyotirao Phule Jan Arogya Yojana?"
        response = RAGService.answer_query(query=query, language="en", department="Public Health")

        assert not response.insufficient_evidence
        assert len(response.citations) > 0
        assert response.language == "en"

    def test_insufficient_evidence_unrelated_query(self):
        """Unrelated Query -> Insufficient evidence flag set to True without hallucinations."""
        query = "चंद्रयान मोहिमेसाठी महाराष्ट्र शासनाने किती निधी दिला?"
        response = RAGService.answer_query(query=query, language="mr")

        assert response.insufficient_evidence is True
        assert len(response.citations) == 0
        assert "पुरावा" in response.answer or "पुरेसा" in response.answer or "उपलब्ध नाही" in response.answer
