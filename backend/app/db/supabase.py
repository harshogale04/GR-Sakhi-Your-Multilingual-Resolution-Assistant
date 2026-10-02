from typing import Optional
from supabase import create_client, Client
from backend.app.core.config import settings
from backend.app.core.logging import logger

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns the Supabase Client singleton.
    Returns None with warning if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning(
            "SUPABASE_URL or SUPABASE_KEY not set. Operating with mocked or deferred database layer."
        )
        return None

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def check_supabase_connection() -> bool:
    """Check connectivity to the Supabase documents table."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        res = client.table("documents").select("id").limit(1).execute()
        return res is not None
    except Exception as e:
        logger.debug(f"Supabase connection check failed: {e}")
        return False


def check_supabase_storage_connection() -> bool:
    """Check connectivity to the existing Supabase storage bucket."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        buckets = client.storage.list_buckets()
        return any(b.name == settings.SUPABASE_STORAGE_BUCKET for b in buckets)
    except Exception as e:
        logger.debug(f"Supabase storage check failed: {e}")
        return False
