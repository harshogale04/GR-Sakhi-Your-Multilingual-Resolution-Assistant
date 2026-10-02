from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.upload import router as upload_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.demo import router as demo_router
from backend.app.services.document_service import DocumentService
from backend.app.schemas.documents import DocumentStatsResponse

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(upload_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(demo_router)


@api_v1_router.get("/stats", response_model=DocumentStatsResponse, tags=["Documents"])
def get_global_stats():
    """Top-level stats endpoint aliasing /documents/stats for convenience."""
    return DocumentService.get_stats()
