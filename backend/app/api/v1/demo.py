"""
Demo Mode API Endpoints for MAHA-GR.
Enables judges and evaluators to inspect demo status, seed representative sample GRs,
and test multilingual RAG without needing live cloud credentials.
"""
from fastapi import APIRouter
from backend.app.services.demo_service import DemoService
from backend.app.db.supabase import check_supabase_connection
from backend.app.db.repositories.document_repository import _mock_documents
from backend.app.db.repositories.chunk_repository import _mock_chunks
from backend.app.services.vector_store_service import _mock_pinecone_store

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


@router.get("/status")
def get_demo_status():
    """Returns demo mode status, seeded sample documents count, and recommended prompts."""
    is_demo = DemoService.is_demo_mode()
    cloud_connected = check_supabase_connection()
    sample_docs_count = sum(1 for d in _mock_documents.values() if d.get("is_sample"))

    return {
        "is_demo_mode": is_demo,
        "cloud_connected": cloud_connected,
        "sample_documents_count": sample_docs_count,
        "total_documents_count": len(_mock_documents),
        "prompts": DemoService.get_sample_prompts(),
        "disclaimer": "Sample documents are representative Maharashtra Government Resolutions used for offline/demo evaluation.",
    }


@router.post("/seed")
def seed_demo_documents():
    """Seeds representative Maharashtra Government Resolutions into the repository."""
    seeded = DemoService.seed_sample_documents()
    return {
        "success": True,
        "seeded_count": seeded,
        "message": f"Successfully seeded {seeded} representative Maharashtra Government Resolutions for demonstration.",
    }


@router.post("/reset")
def reset_demo_documents():
    """Resets the mock repository to a clean seeded demo state."""
    _mock_documents.clear()
    _mock_chunks.clear()
    _mock_pinecone_store.clear()
    seeded = DemoService.seed_sample_documents()
    return {
        "success": True,
        "seeded_count": seeded,
        "message": "Repository reset and re-seeded with representative demo resolutions.",
    }
