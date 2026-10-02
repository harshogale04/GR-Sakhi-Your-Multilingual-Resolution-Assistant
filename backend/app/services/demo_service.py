"""
Demo Mode Service for MAHA-GR.
Enables full exploration and demonstration of the platform even when external cloud
credentials (Supabase, Pinecone, Gemini API) are not configured.

Provides:
- Realistic, clearly labeled sample Maharashtra Government Resolutions (labeled with [नमुना GR]).
- Complete relational metadata for PostgreSQL documents and chunks tables.
- Real 768-dimensional embeddings for local vector retrieval.
- Realistic sample PDF file bytes in mock storage for PDF preview/download.
- Trilingual sample questions (Marathi, Hindi, English) with grounded answers.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from backend.app.core.logging import logger
from backend.app.db.supabase import check_supabase_connection
from backend.app.db.repositories.document_repository import _mock_documents
from backend.app.db.repositories.chunk_repository import _mock_chunks
from backend.app.services.storage_service import _mock_storage_bucket
from backend.app.services.vector_store_service import _mock_pinecone_store
from backend.app.services.embedding_service import EmbeddingService

# Fixed UUIDs for predictable demo exploration
DEMO_DOC_1_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_DOC_2_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_DOC_3_ID = UUID("33333333-3333-4333-8333-333333333333")

def _make_sample_pdf_bytes(title: str, text: str) -> bytes:
    """Creates minimal valid PDF bytes representing a sample government resolution."""
    content_escaped = text.replace("(", "[").replace(")", "]")[:400]
    stream_content = f"BT /F1 12 Tf 50 700 Td ({title}) Tj 0 -20 Td ({content_escaped}) Tj ET".encode("latin-1", "replace")
    stream_len = len(stream_content)
    
    header = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    stream_obj = f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("ascii") + stream_content + b"\nendstream\nendobj\n"
    footer = (
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000242 00000 n \n"
        b"0000000350 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n430\n%%EOF"
    )
    return header + stream_obj + footer


SAMPLE_GRS = [
    {
        "id": DEMO_DOC_1_ID,
        "filename": "sample_agri_gr_2024_drip_subsidy.pdf",
        "original_filename": "AGRI_GR_2024_08_15_Drip_Subsidy.pdf",
        "storage_path": "resolutions/demo_agri_drip_subsidy_2024.pdf",
        "status": "COMPLETED",
        "category": "Scheme",
        "department": "Agriculture",
        "language": "mr",
        "document_type": "Government Resolution",
        "subject": "[नमुना GR] महात्मा ज्योतिराव फुले शेतकरी कर्जमुक्ती योजना व ठिबक सिंचन अनुदान नियमावली २०२४",
        "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
        "pages": 3,
        "chunk_count": 4,
        "uploaded_at": "2024-08-15T10:30:00Z",
        "is_sample": True,
        "chunks": [
            {
                "chunk_id": f"{DEMO_DOC_1_ID}_p1_c1",
                "page": 1,
                "section": "शासन निर्णय / Resolution",
                "text": "शासन निर्णय: राज्यातील दुष्काळग्रस्त व अवकाळी पाऊस बाधित तालुक्यांमधील शेतकऱ्यांसाठी ठिबक सिंचन योजनेअंतर्गत विशेष अनुदान मंजूर करण्यात येत आहे. अल्प व अत्यल्प भूधारक शेतकऱ्यांना ८०% अनुदान आणि इतर शेतकऱ्यांना ७०% अनुदान थेट बँक खात्यात (DBT) जमा केले जाईल.",
            },
            {
                "chunk_id": f"{DEMO_DOC_1_ID}_p2_c1",
                "page": 2,
                "section": "पात्रता / Eligibility",
                "text": "पात्रतेचे निकष: १. अर्जदार शेतकऱ्याचे आधार प्रमाणीकरण (e-KYC) पूर्ण असणे आवश्यक आहे. २. शेतकऱ्याच्या नावावर ७/१२ आणि ८-अ उतारा असणे बंधनकारक आहे. ३. शेतात कार्यान्वित वीज जोडणी किंवा सौर कृषी पंप असणे आवश्यक आहे. ४. महाडीबीटी पोर्टलवर (MahaDBT) विहित मुदतीत ऑनलाईन अर्ज करणे आवश्यक आहे.",
            },
            {
                "chunk_id": f"{DEMO_DOC_1_ID}_p3_c1",
                "page": 3,
                "section": "कार्यपद्धती व अंतिम मुदत / Procedure",
                "text": "कार्यपद्धती व अंतिम मुदत: योजनेसाठी अर्ज करण्याची अंतिम मुदत ३१ डिसेंबर २०२४ रोजी सायंकाळी ५:०० वाजेपर्यंत राहील. तालुका कृषी अधिकारी कार्यालयामार्फत कागदपत्रांची प्राथमिक छाननी १५ दिवसांत केली जाईल व पात्र शेतकऱ्यांना पूर्वसंमती दिली जाईल.",
            },
            {
                "chunk_id": f"{DEMO_DOC_1_ID}_p3_c2",
                "page": 3,
                "section": "अटी व अपवाद / Exceptions",
                "text": "महत्त्वाच्या अटी व अपवाद: ज्या शेतकऱ्यांनी मागील ३ वर्षांत कोणत्याही शासकीय ठिबक किंवा तुषार सिंचन योजनेचा लाभ घेतला आहे, ते शेतकरी या योजनेसाठी अपात्र ठरतील. एका कुटुंबातील केवळ एकाच व्यक्तीला अनुदानाचा लाभ अनुज्ञेय राहील.",
            },
        ],
    },
    {
        "id": DEMO_DOC_2_ID,
        "filename": "sample_edu_gr_2024_rte_admission.pdf",
        "original_filename": "EDU_GR_2024_RTE_Admission_Guidelines.pdf",
        "storage_path": "resolutions/demo_edu_rte_admission_2024.pdf",
        "status": "COMPLETED",
        "category": "Policy",
        "department": "School Education",
        "language": "mr",
        "document_type": "Government Resolution",
        "subject": "[नमुना GR] शालेय शिक्षण विभाग - आरटीई २५% प्रवेश प्रक्रिया व दुर्बल घटक शुल्क प्रतिपूर्ती",
        "gr_number": "आर.टी.ई.-२०२४/प्र.क्र.१२४/एसडी-२",
        "pages": 2,
        "chunk_count": 2,
        "uploaded_at": "2024-05-10T11:00:00Z",
        "is_sample": True,
        "chunks": [
            {
                "chunk_id": f"{DEMO_DOC_2_ID}_p1_c1",
                "page": 1,
                "section": "प्रवेश नियम / Guidelines",
                "text": "बालकांचा मोफत व सक्तीच्या शिक्षणाचा हक्क अधिनियम (RTE) अंतर्गत खाजगी विनाअनुदानित शाळांमध्ये २५% जागांवर सामाजिक व शैक्षणिकदृष्ट्या वंचित व आर्थिकदृष्ट्या दुर्बल घटकातील पाल्यांसाठी मोफत प्रवेश प्रक्रिया राबविण्यात येत आहे. दुर्बल घटकासाठी पालकांची वार्षिक उत्पन्न मर्यादा १ लाख रुपये इतकी निश्चित करण्यात आली आहे.",
            },
            {
                "chunk_id": f"{DEMO_DOC_2_ID}_p2_c1",
                "page": 2,
                "section": "नोंदणी मुदत / Schedule",
                "text": "शाळांची पडताळणी व पालकांची ऑनलाईन अर्ज नोंदणी १५ मे २०२४ पर्यंत पूर्ण करणे बंधनकारक आहे. जिल्हा शिक्षणाधिकारी (प्राथमिक) यांच्या अध्यक्षतेखालील समितीमार्फत पारदर्शक संगणकीय सोडत (लॉटरी) काढून विद्यार्थ्यांची निवड केली जाईल.",
            },
        ],
    },
    {
        "id": DEMO_DOC_3_ID,
        "filename": "sample_health_gr_2023_mjpjay.pdf",
        "original_filename": "HEALTH_GR_MJPJAY_Treatment_Coverage.pdf",
        "storage_path": "resolutions/demo_health_mjpjay_2023.pdf",
        "status": "COMPLETED",
        "category": "Scheme",
        "department": "Public Health",
        "language": "mr",
        "document_type": "Government Resolution",
        "subject": "[नमुना GR] महात्मा ज्योतिराव फुले जन आरोग्य योजना (MJPJAY) - विशेष वैद्यकीय उपचार व रुग्णालय मान्यता नियमावली",
        "gr_number": "आरोग्य-२०२३/प्र.क्र.५१२/कु.क.-३",
        "pages": 2,
        "chunk_count": 2,
        "uploaded_at": "2023-11-20T14:15:00Z",
        "is_sample": True,
        "chunks": [
            {
                "chunk_id": f"{DEMO_DOC_3_ID}_p1_c1",
                "page": 1,
                "section": "उपचार मर्यादा / Benefits",
                "text": "महात्मा ज्योतिराव फुले जन आरोग्य योजना आणि आयुष्यमान भारत प्रधानमंत्री जन आरोग्य योजना यांच्या एकत्रित अंमलबजावणीद्वारे राज्यातील सर्व रेशनकार्डधारक कुटुंबांना प्रति कुटुंब प्रति वर्ष ५ लाख रुपयांपर्यंत मोफत वैद्यकीय उपचार व शस्त्रक्रिया सुविधा उपलब्ध करून देण्यात येत आहे.",
            },
            {
                "chunk_id": f"{DEMO_DOC_3_ID}_p2_c1",
                "page": 2,
                "section": "अंगीकृत रुग्णालये / Hospitals",
                "text": "सार्वजनिक आरोग्य विभागामार्फत राज्यातील १,००० हून अधिक शासनमान्य शासकीय व खाजगी रुग्णालयांमध्ये ही सुविधा कॅशलेस पद्धतीने दिली जाईल. उपचारासाठी आधार कार्ड व वैध शिधापत्रिका (पिवळी, केशरी किंवा पांढरी) सादर करणे आवश्यक आहे.",
            },
        ],
    },
]


class DemoService:
    """Service providing demo mode seeding, status, and sample data."""

    @classmethod
    def is_demo_mode(cls) -> bool:
        """Determines if the application is currently running in offline/demo mode."""
        supabase_connected = check_supabase_connection()
        return not supabase_connected

    @classmethod
    def seed_sample_documents(cls) -> int:
        """
        Seeds representative Maharashtra Government Resolutions into in-memory repositories
        when cloud database is offline, ensuring the platform is immediately demonstrable.
        """
        seeded_count = 0
        for doc_data in SAMPLE_GRS:
            doc_id = doc_data["id"]
            doc_id_str = str(doc_id)

            # 1. Document record in mock repository
            _mock_documents[doc_id_str] = {
                "id": doc_id,
                "filename": doc_data["filename"],
                "original_filename": doc_data["original_filename"],
                "storage_path": doc_data["storage_path"],
                "status": doc_data["status"],
                "category": doc_data["category"],
                "department": doc_data["department"],
                "language": doc_data["language"],
                "document_type": doc_data["document_type"],
                "subject": doc_data["subject"],
                "gr_number": doc_data["gr_number"],
                "pages": doc_data["pages"],
                "chunk_count": doc_data["chunk_count"],
                "uploaded_at": doc_data["uploaded_at"],
                "is_sample": True,
            }

            # 2. PDF file in mock storage bucket
            if doc_data["storage_path"] not in _mock_storage_bucket:
                pdf_bytes = _make_sample_pdf_bytes(doc_data["subject"], doc_data["chunks"][0]["text"])
                _mock_storage_bucket[doc_data["storage_path"]] = pdf_bytes

            # 3. Chunks in relational mock chunks repository & Pinecone vector store
            for chk in doc_data["chunks"]:
                pinecone_id = f"vec_{chk['chunk_id']}"
                chunk_uuid = UUID(int=hash(chk["chunk_id"]) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

                # Relational chunk
                _mock_chunks[str(chunk_uuid)] = {
                    "id": chunk_uuid,
                    "chunk_id": chk["chunk_id"],
                    "document_id": doc_id,
                    "page": chk["page"],
                    "section": chk["section"],
                    "pinecone_id": pinecone_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                # Pinecone vector store
                if pinecone_id not in _mock_pinecone_store:
                    embedding = EmbeddingService.get_document_embedding(chk["text"])
                    _mock_pinecone_store[pinecone_id] = {
                        "id": pinecone_id,
                        "values": embedding,
                        "metadata": {
                            "document_id": doc_id_str,
                            "chunk_id": chk["chunk_id"],
                            "text": chk["text"],
                            "page": chk["page"],
                            "section": chk["section"],
                            "language": doc_data["language"],
                            "filename": doc_data["original_filename"],
                            "gr_number": doc_data["gr_number"],
                            "department": doc_data["department"],
                            "is_sample": True,
                        },
                    }

            seeded_count += 1

        logger.info(f"Demo Mode: Successfully seeded {seeded_count} representative Maharashtra GR documents.")
        return seeded_count

    @classmethod
    def get_sample_prompts(cls) -> Dict[str, List[str]]:
        return {
            "mr": [
                "ठिबक सिंचन योजनेअंतर्गत शेतकऱ्यांना किती टक्के अनुदान मिळते?",
                "ठिबक सिंचन अनुदानासाठी अर्ज करण्याची अंतिम मुदत कोणती आहे?",
                "शेतकरी अनुदानासाठी कोणती कागदपत्रे व पात्रता अटी आवश्यक आहेत?",
                "पूर्वी लाभ घेतलेल्या शेतकऱ्यांना पुन्हा कधी अर्ज करता येईल?",
                "आरटीई (RTE) २५% प्रवेशासाठी पालकांची वार्षिक उत्पन्न मर्यादा किती आहे?",
                "महात्मा ज्योतिराव फुले जन आरोग्य योजनेअंतर्गत प्रति कुटुंब किती रकमेचे उपचार मोफत मिळतात?",
            ],
            "hi": [
                "ड्रिप सिंचाई योजना के तहत किसानों को कितनी सब्सिडी दी जाती है?",
                "ड्रिप सब्सिडी के लिए आवेदन करने की अंतिम तिथि क्या है?",
                "आरटीई 25% प्रवेश के लिए माता-पिता की वार्षिक आय सीमा क्या है?",
                "महात्मा ज्योतिराव फुले जन आरोग्य योजना में कितना मुफ्त इलाज मिलता है?",
            ],
            "en": [
                "What percentage of drip irrigation subsidy is granted to small farmers?",
                "What is the deadline for applying to the drip irrigation scheme?",
                "What is the annual income limit for 25% RTE admissions?",
                "What is the annual coverage limit under MJPJAY health scheme?",
            ],
        }
