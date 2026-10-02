from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse, ServiceHealthStatus
from backend.app.db.supabase import check_supabase_connection, check_supabase_storage_connection
from backend.app.db.pinecone import check_pinecone_connection

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """
    Health check endpoint returning system status and status of connected services:
    - Supabase PostgreSQL (documents/chunks tables)
    - Supabase Storage (resolutions bucket)
    - Pinecone Vector Database
    - Google Gemini AI
    """
    supabase_db_ok = check_supabase_connection()
    supabase_storage_ok = check_supabase_storage_connection()
    pinecone_ok = check_pinecone_connection()
    gemini_ok = bool(settings.GEMINI_API_KEY)
    is_demo = not supabase_db_ok

    return HealthResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        is_demo_mode=is_demo,
        timestamp=datetime.now(timezone.utc),
        services=ServiceHealthStatus(
            supabase_db=supabase_db_ok,
            supabase_storage=supabase_storage_ok,
            pinecone=pinecone_ok,
            gemini_api=gemini_ok,
        ),
    )
