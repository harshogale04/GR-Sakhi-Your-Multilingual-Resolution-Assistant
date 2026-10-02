from typing import Optional, Any
from pinecone import Pinecone
from backend.app.core.config import settings
from backend.app.core.logging import logger

_pinecone_client: Optional[Pinecone] = None
_pinecone_index: Optional[Any] = None


def get_pinecone_client() -> Optional[Pinecone]:
    global _pinecone_client
    if _pinecone_client is not None:
        return _pinecone_client

    if not settings.PINECONE_API_KEY:
        logger.warning("PINECONE_API_KEY is not configured.")
        return None

    try:
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        logger.info("Pinecone client initialized successfully.")
        return _pinecone_client
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone client: {e}")
        return None


def get_pinecone_index() -> Optional[Any]:
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    pc = get_pinecone_client()
    if not pc:
        return None

    try:
        _pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)
        return _pinecone_index
    except Exception as e:
        logger.error(f"Failed to connect to Pinecone index '{settings.PINECONE_INDEX_NAME}': {e}")
        return None


def check_pinecone_connection() -> bool:
    try:
        pc = get_pinecone_client()
        if not pc:
            return False
        indexes = pc.list_indexes()
        return any(idx.name == settings.PINECONE_INDEX_NAME for idx in indexes)
    except Exception as e:
        logger.debug(f"Pinecone connection check failed: {e}")
        return False
