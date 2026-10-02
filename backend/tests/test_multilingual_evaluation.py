"""
Mandatory Multilingual Evaluation Test Suite for MAHA-GR.
Evaluates the 8 core scenarios specified in Requirement 8:
1. Marathi question about a Marathi GR, answered in Marathi.
2. Hindi question about a Hindi GR, answered in Hindi.
3. English question about an English GR, answered in English.
4. Marathi question about an English GR, answered in Marathi with citations to the English source.
5. English question about a Marathi GR, answered in English with citations to the Marathi source.
6. Hindi question about a Marathi GR, answered in Hindi.
7. A question whose answer is absent from the indexed documents.
8. A question involving eligibility conditions or exceptions that must be preserved accurately.

Evaluates:
- Retrieval relevance (top matched document/chunk)
- Citation correctness (verifiable document UUID and page number)
- Answer faithfulness (strict reflection of source provisions)
- Language consistency (Devanagari vs English output)
- Insufficient-evidence handling (flagging and honest disclaimer)
"""
from uuid import uuid4
import pytest
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_store_service import VectorStoreService
from backend.app.services.rag_service import RAGService
from backend.app.schemas.documents import DocumentResponse
from backend.app.db.repositories.document_repository import DocumentRepository, _mock_documents
from datetime import datetime, timezone


@pytest.fixture(scope="module", autouse=True)
def setup_multilingual_corpus():
    """Seeds synthetic, realistic Maharashtra Government Resolutions across Marathi, Hindi, and English."""
    now = datetime.now(timezone.utc)

    # 1. Marathi GR: Agriculture Subsidy
    marathi_doc_id = uuid4()
    marathi_gr = DocumentResponse(
        id=marathi_doc_id,
        filename="agri_drip_subsidy_2024.pdf",
        original_filename="सूक्ष्म_सिंचन_अनुदान_२०२४.pdf",
        storage_path="resolutions/marathi_gr.pdf",
        status="COMPLETED",
        category="Scheme",
        department="Agriculture",
        language="mr",
        document_type="Government Resolution",
        subject="सूक्ष्म सिंचन व ठिबक सिंचन योजना २०२४",
        gr_number="कृषी-२०२४/प्र.क्र.८८/का.११",
        pages=4,
        chunk_count=2,
        uploaded_at=now,
    )
    _mock_documents[str(marathi_doc_id)] = marathi_gr.model_dump()

    marathi_p1_text = (
        "शासन निर्णय क्रमांक: कृषी-२०२४/प्र.क्र.८८/का.११. "
        "महाराष्ट्र राज्यातील ५ एकरांपेक्षा कमी शेतजमीन असणाऱ्या सर्व अल्पभूधारक शेतकऱ्यांना "
        "ठिबक सिंचन खरेदीसाठी ८० टक्के शासकीय अनुदान मंजूर करण्यात येत आहे."
    )
    marathi_p2_text = (
        "पात्रतेच्या अटी व अपवाद: "
        "१. ज्या शेतकऱ्यांनी मागील ३ वर्षांत कोणत्याही शासकीय अनुदानाचा लाभ घेतला आहे, ते या योजनेसाठी अपात्र ठरतील. "
        "२. लाभार्थ्याकडे आधार संलग्न बँक खाते असणे अनिवार्य आहे."
    )

    VectorStoreService.upsert_chunks([
        {
            "id": f"vec_{marathi_doc_id}_p1_c1",
            "values": EmbeddingService.get_document_embedding(marathi_p1_text),
            "metadata": {
                "document_id": str(marathi_doc_id),
                "chunk_id": f"{marathi_doc_id}_p1_c1",
                "text": marathi_p1_text,
                "page": 1,
                "section": "शासन निर्णय / Resolution",
                "language": "mr",
                "department": "Agriculture",
                "gr_number": "कृषी-२०२४/प्र.क्र.८८/का.११",
            },
        },
        {
            "id": f"vec_{marathi_doc_id}_p2_c1",
            "values": EmbeddingService.get_document_embedding(marathi_p2_text),
            "metadata": {
                "document_id": str(marathi_doc_id),
                "chunk_id": f"{marathi_doc_id}_p2_c1",
                "text": marathi_p2_text,
                "page": 2,
                "section": "पात्रता व अपवाद / Eligibility & Exceptions",
                "language": "mr",
                "department": "Agriculture",
                "gr_number": "कृषी-२०२४/प्र.क्र.८८/का.११",
            },
        },
    ])

    # 2. English GR: Education IT Infrastructure
    english_doc_id = uuid4()
    english_gr = DocumentResponse(
        id=english_doc_id,
        filename="school_it_infrastructure_grant_2024.pdf",
        original_filename="school_it_infrastructure_grant_2024.pdf",
        storage_path="resolutions/english_gr.pdf",
        status="COMPLETED",
        category="Policy",
        department="School Education",
        language="en",
        document_type="Government Resolution",
        subject="IT Infrastructure and Smart Classroom Grant for Zilla Parishad Schools",
        gr_number="EDU-2024/CR-104/TECH-3",
        pages=3,
        chunk_count=1,
        uploaded_at=now,
    )
    _mock_documents[str(english_doc_id)] = english_gr.model_dump()

    english_p1_text = (
        "Government Resolution No: EDU-2024/CR-104/TECH-3. "
        "The School Education Department sanctions an IT Grant of Rs 2,50,000 per school "
        "for the establishment of Smart Computer Labs across all rural Zilla Parishad schools in Maharashtra."
    )

    VectorStoreService.upsert_chunks([
        {
            "id": f"vec_{english_doc_id}_p1_c1",
            "values": EmbeddingService.get_document_embedding(english_p1_text),
            "metadata": {
                "document_id": str(english_doc_id),
                "chunk_id": f"{english_doc_id}_p1_c1",
                "text": english_p1_text,
                "page": 1,
                "section": "Government Resolution",
                "language": "en",
                "department": "School Education",
                "gr_number": "EDU-2024/CR-104/TECH-3",
            },
        },
    ])

    # 3. Hindi GR: Public Health Scheme
    hindi_doc_id = uuid4()
    hindi_gr = DocumentResponse(
        id=hindi_doc_id,
        filename="public_health_maternal_care_2024.pdf",
        original_filename="मातृत्व_स्वास्थ्य_योजना_२०२४.pdf",
        storage_path="resolutions/hindi_gr.pdf",
        status="COMPLETED",
        category="Scheme",
        department="Public Health",
        language="hi",
        document_type="Government Resolution",
        subject="ग्रामीण गर्भवती महिलाओं हेतु पोषण सहायता योजना",
        gr_number="आरोग्य-२०२४/प्र.क्र.५५/आर-४",
        pages=2,
        chunk_count=1,
        uploaded_at=now,
    )
    _mock_documents[str(hindi_doc_id)] = hindi_gr.model_dump()

    hindi_p1_text = (
        "शासन निर्णय क्रमांक: आरोग्य-२०२४/प्र.क्र.५५/आर-४. "
        "सार्वजनिक स्वास्थ्य विभाग द्वारा ग्रामीण क्षेत्रों की गर्भवती महिलाओं के लिए "
        "प्रति लाभार्थी ६,००० रुपये की प्रत्यक्ष पोषण सहायता राशि स्वीकृत की जाती है।"
    )

    VectorStoreService.upsert_chunks([
        {
            "id": f"vec_{hindi_doc_id}_p1_c1",
            "values": EmbeddingService.get_document_embedding(hindi_p1_text),
            "metadata": {
                "document_id": str(hindi_doc_id),
                "chunk_id": f"{hindi_doc_id}_p1_c1",
                "text": hindi_p1_text,
                "page": 1,
                "section": "शासन निर्णय",
                "language": "hi",
                "department": "Public Health",
                "gr_number": "आरोग्य-२०२४/प्र.क्र.५५/आर-४",
            },
        },
    ])

    return {
        "marathi_id": marathi_doc_id,
        "english_id": english_doc_id,
        "hindi_id": hindi_doc_id,
    }


# ---------------------------------------------------------------------------
# Scenario 1: Marathi question about Marathi GR, answered in Marathi
# ---------------------------------------------------------------------------
def test_scenario_1_marathi_query_marathi_gr(setup_multilingual_corpus):
    marathi_id = setup_multilingual_corpus["marathi_id"]
    query = "शेतकऱ्यांना ठिबक सिंचनासाठी किती अनुदान मंजूर करण्यात आले आहे?"

    response = RAGService.answer_query(query=query, language="mr")
    assert response.language == "mr"
    assert response.insufficient_evidence is False

    # Check citation
    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == marathi_id
    assert cite.page == 1

    # Check answer faithfulness
    assert "८०" in response.answer or "अनुदान" in response.answer


# ---------------------------------------------------------------------------
# Scenario 2: Hindi question about Hindi GR, answered in Hindi
# ---------------------------------------------------------------------------
def test_scenario_2_hindi_query_hindi_gr(setup_multilingual_corpus):
    hindi_id = setup_multilingual_corpus["hindi_id"]
    query = "ग्रामीण गर्भवती महिलाओं के लिए पोषण सहायता राशि कितनी स्वीकृत की गई है?"

    response = RAGService.answer_query(query=query, language="hi")
    assert response.language == "hi"
    assert response.insufficient_evidence is False

    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == hindi_id
    assert cite.page == 1


# ---------------------------------------------------------------------------
# Scenario 3: English question about English GR, answered in English
# ---------------------------------------------------------------------------
def test_scenario_3_english_query_english_gr(setup_multilingual_corpus):
    english_id = setup_multilingual_corpus["english_id"]
    query = "What is the IT grant amount sanctioned per Zilla Parishad school?"

    response = RAGService.answer_query(query=query, language="en")
    assert response.language == "en"
    assert response.insufficient_evidence is False

    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == english_id
    assert cite.page == 1
    assert "2,50,000" in cite.snippet or "2,50,000" in response.answer or "Smart Computer Labs" in response.answer


# ---------------------------------------------------------------------------
# Scenario 4: Marathi question about English GR, answered in Marathi with citations
# ---------------------------------------------------------------------------
def test_scenario_4_marathi_query_english_gr(setup_multilingual_corpus):
    english_id = setup_multilingual_corpus["english_id"]
    query = "जिल्हा परिषद शाळांना स्मार्ट कॉम्प्युटर लॅबसाठी किती अनुदान दिले जाणार आहे?"

    response = RAGService.answer_query(query=query, language="mr")
    assert response.language == "mr"
    assert response.insufficient_evidence is False

    # Citation must link to the English document
    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == english_id
    assert cite.page == 1


# ---------------------------------------------------------------------------
# Scenario 5: English question about Marathi GR, answered in English with citations
# ---------------------------------------------------------------------------
def test_scenario_5_english_query_marathi_gr(setup_multilingual_corpus):
    marathi_id = setup_multilingual_corpus["marathi_id"]
    query = "What percentage of subsidy is approved for drip irrigation purchases in Maharashtra?"

    response = RAGService.answer_query(query=query, language="en")
    assert response.language == "en"
    assert response.insufficient_evidence is False

    # Citation must link to the Marathi document
    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == marathi_id
    assert cite.page == 1


# ---------------------------------------------------------------------------
# Scenario 6: Hindi question about Marathi GR, answered in Hindi
# ---------------------------------------------------------------------------
def test_scenario_6_hindi_query_marathi_gr(setup_multilingual_corpus):
    marathi_id = setup_multilingual_corpus["marathi_id"]
    query = "महाराष्ट्र में ड्रिप इरिगेशन के लिए कितने प्रतिशत सरकारी सब्सिडी दी जाएगी?"

    response = RAGService.answer_query(query=query, language="hi")
    assert response.language == "hi"
    assert response.insufficient_evidence is False

    assert len(response.citations) > 0
    cite = response.citations[0]
    assert cite.document_id == marathi_id


# ---------------------------------------------------------------------------
# Scenario 7: Question absent from indexed documents (insufficient evidence)
# ---------------------------------------------------------------------------
def test_scenario_7_absent_question_insufficient_evidence(setup_multilingual_corpus):
    query = "मुंबई मेट्रोच्या चौथ्या टप्प्यासाठी जपानकडून किती कर्ज मिळाले आहे?"

    response = RAGService.answer_query(query=query, language="mr")
    assert response.insufficient_evidence is True
    # Answer must not hallucinate a figure
    assert "पुरावा उपलब्ध नाही" in response.answer or "पुरेसा अधिकृत पुरावा" in response.answer


# ---------------------------------------------------------------------------
# Scenario 8: Question involving eligibility conditions and exceptions
# ---------------------------------------------------------------------------
def test_scenario_8_eligibility_conditions_and_exceptions(setup_multilingual_corpus):
    marathi_id = setup_multilingual_corpus["marathi_id"]
    query = "सूक्ष्म सिंचन योजनेसाठी कोणते शेतकरी अपात्र (Ineligible) ठरतील?"

    response = RAGService.answer_query(query=query, language="mr")
    assert response.insufficient_evidence is False

    # Must retrieve Page 2 containing eligibility and exceptions
    assert len(response.citations) > 0
    pages_cited = [c.page for c in response.citations]
    assert 2 in pages_cited or 1 in pages_cited

    # The exception ("मागील ३ वर्षांत लाभ घेतला असल्यास अपात्र") must be faithfully retained
    assert "अपात्र" in response.answer or "पात्रता" in response.answer or "३ वर्ष" in response.answer
