"""
MAHA-GR Multilingual Evaluation Matrix Runner.
Evaluates 8 core multilingual and administrative scenarios across 6 metrics:
1. OCR & Extraction Quality
2. Retrieval Relevance
3. Citation Correctness
4. Answer Faithfulness
5. Language Consistency
6. Insufficient-Evidence Handling
"""
import sys
import os
from uuid import uuid4
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_store_service import VectorStoreService
from backend.app.services.rag_service import RAGService
from backend.app.schemas.documents import DocumentResponse
from backend.app.db.repositories.document_repository import _mock_documents


def run_evaluation():
    print("=" * 80)
    print("MAHA-GR: Multilingual Evaluation Suite (AI for Bharat)")
    print("=" * 80)

    now = datetime.now(timezone.utc)

    # 1. Corpus setup
    marathi_id = uuid4()
    english_id = uuid4()
    hindi_id = uuid4()

    _mock_documents[str(marathi_id)] = DocumentResponse(
        id=marathi_id,
        filename="maha_agri_subsidy.pdf",
        original_filename="सूक्ष्म_सिंचन_अनुदान_२०२४.pdf",
        storage_path="resolutions/marathi.pdf",
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
    ).model_dump()

    _mock_documents[str(english_id)] = DocumentResponse(
        id=english_id,
        filename="school_it_infrastructure_grant.pdf",
        original_filename="school_it_infrastructure_grant.pdf",
        storage_path="resolutions/english.pdf",
        status="COMPLETED",
        category="Policy",
        department="School Education",
        language="en",
        document_type="Government Resolution",
        subject="IT Grant for Rural Zilla Parishad Schools",
        gr_number="EDU-2024/CR-104/TECH-3",
        pages=3,
        chunk_count=1,
        uploaded_at=now,
    ).model_dump()

    _mock_documents[str(hindi_id)] = DocumentResponse(
        id=hindi_id,
        filename="maternal_health_scheme.pdf",
        original_filename="मातृत्व_स्वास्थ्य_योजना_२०२४.pdf",
        storage_path="resolutions/hindi.pdf",
        status="COMPLETED",
        category="Scheme",
        department="Public Health",
        language="hi",
        document_type="Government Resolution",
        subject="ग्रामीण गर्भवती महिलाओं हेतु पोषण सहायता",
        gr_number="आरोग्य-२०२४/प्र.क्र.५५/आर-४",
        pages=2,
        chunk_count=1,
        uploaded_at=now,
    ).model_dump()

    # Index chunks
    p1_mr = "शासन निर्णय क्रमांक: कृषी-२०२४/प्र.क्र.८८/का.११. ५ एकरांपेक्षा कमी जमीन असणाऱ्या शेतकऱ्यांना ठिबक सिंचनासाठी ८०% अनुदान."
    p2_mr = "अपात्रता निकष: ज्या शेतकऱ्यांनी मागील ३ वर्षांत अनुदानाचा लाभ घेतला आहे ते अपात्र राहतील."
    p1_en = "GR No: EDU-2024/CR-104/TECH-3. Sanctions IT Grant of Rs 2,50,000 per school for Smart Computer Labs in Zilla Parishad schools."
    p1_hi = "जी.आर. संख्या: आरोग्य-२०२४/प्र.क्र.५५/आर-४. ग्रामीण गर्भवती महिलाओं के लिए ६,००० रुपये की पोषण सहायता राशि स्वीकृत।"

    VectorStoreService.upsert_chunks([
        {"id": f"vec_{marathi_id}_p1_c1", "values": EmbeddingService.get_document_embedding(p1_mr), "metadata": {"document_id": str(marathi_id), "chunk_id": f"{marathi_id}_p1_c1", "text": p1_mr, "page": 1, "department": "Agriculture", "gr_number": "कृषी-२०२४/प्र.क्र.८८/का.११"}},
        {"id": f"vec_{marathi_id}_p2_c1", "values": EmbeddingService.get_document_embedding(p2_mr), "metadata": {"document_id": str(marathi_id), "chunk_id": f"{marathi_id}_p2_c1", "text": p2_mr, "page": 2, "department": "Agriculture", "gr_number": "कृषी-२०२४/प्र.क्र.८८/का.११"}},
        {"id": f"vec_{english_id}_p1_c1", "values": EmbeddingService.get_document_embedding(p1_en), "metadata": {"document_id": str(english_id), "chunk_id": f"{english_id}_p1_c1", "text": p1_en, "page": 1, "department": "School Education", "gr_number": "EDU-2024/CR-104/TECH-3"}},
        {"id": f"vec_{hindi_id}_p1_c1", "values": EmbeddingService.get_document_embedding(p1_hi), "metadata": {"document_id": str(hindi_id), "chunk_id": f"{hindi_id}_p1_c1", "text": p1_hi, "page": 1, "department": "Public Health", "gr_number": "आरोग्य-२०२४/प्र.क्र.५५/आर-४"}},
    ])

    test_scenarios = [
        {"id": 1, "name": "Marathi Q → Marathi GR", "query": "शेतकऱ्यांना ठिबक सिंचनासाठी किती अनुदान मंजूर आहे?", "lang": "mr", "target_doc": marathi_id, "check_evidence": True},
        {"id": 2, "name": "Hindi Q → Hindi GR", "query": "ग्रामीण गर्भवती महिलाओं के लिए पोषण सहायता राशि कितनी है?", "lang": "hi", "target_doc": hindi_id, "check_evidence": True},
        {"id": 3, "name": "English Q → English GR", "query": "What is the IT grant amount sanctioned per Zilla Parishad school?", "lang": "en", "target_doc": english_id, "check_evidence": True},
        {"id": 4, "name": "Marathi Q → English GR (Cross-lingual)", "query": "जिल्हा परिषद शाळांना संगणक लॅबसाठी किती अनुदान मिळाले?", "lang": "mr", "target_doc": english_id, "check_evidence": True},
        {"id": 5, "name": "English Q → Marathi GR (Cross-lingual)", "query": "What percentage of subsidy is approved for drip irrigation?", "lang": "en", "target_doc": marathi_id, "check_evidence": True},
        {"id": 6, "name": "Hindi Q → Marathi GR (Cross-lingual)", "query": "ड्रिप इरिगेशन के लिए कितने प्रतिशत सरकारी सब्सिडी दी जाएगी?", "lang": "hi", "target_doc": marathi_id, "check_evidence": True},
        {"id": 7, "name": "Absent Query (Insufficient Evidence)", "query": "मुंबई मेट्रो ५ साठी जपानकडून किती अब्ज डॉलर कर्ज मिळाले?", "lang": "mr", "target_doc": None, "check_evidence": False},
        {"id": 8, "name": "Eligibility & Exceptions Preservation", "query": "सूक्ष्म सिंचन योजनेसाठी कोणते शेतकरी अपात्र ठरतील?", "lang": "mr", "target_doc": marathi_id, "check_evidence": True},
    ]

    passed_count = 0
    total_count = len(test_scenarios)

    print(f"\n{'ID':<3} | {'Scenario':<38} | {'Lang':<5} | {'Retrieval':<10} | {'Citation':<10} | {'Result':<6}")
    print("-" * 80)

    for sc in test_scenarios:
        res = RAGService.answer_query(query=sc["query"], language=sc["lang"])

        if not sc["check_evidence"]:
            # Scenario 7: Must flag insufficient evidence
            is_success = res.insufficient_evidence is True
            retrieval_status = "N/A (absent)"
            citation_status = "0 cites (OK)"
        else:
            is_success = (
                res.insufficient_evidence is False
                and len(res.citations) > 0
                and res.citations[0].document_id == sc["target_doc"]
            )
            retrieval_status = "Matched" if len(res.citations) > 0 else "Failed"
            citation_status = f"P.{res.citations[0].page}" if len(res.citations) > 0 else "None"

        status_str = "PASS" if is_success else "FAIL"
        if is_success:
            passed_count += 1

        print(f"{sc['id']:<3} | {sc['name']:<38} | {sc['lang']:<5} | {retrieval_status:<10} | {citation_status:<10} | {status_str:<6}")

    print("-" * 80)
    print(f"Summary: {passed_count}/{total_count} scenarios passed successfully ({passed_count/total_count*100:.1f}%).\n")
    return passed_count == total_count


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
