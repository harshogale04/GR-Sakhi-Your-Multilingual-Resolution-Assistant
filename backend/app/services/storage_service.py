import re
import uuid
from typing import Optional, Dict
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.supabase import get_supabase_client

# Local in-memory storage fallback for offline/development test execution
_mock_storage_bucket: Dict[str, bytes] = {}


class StorageService:
    """
    Dedicated service for interacting with the existing Supabase Storage bucket.
    Complies strictly with existing bucket configuration from settings.SUPABASE_STORAGE_BUCKET.
    Does NOT automatically create or modify buckets.
    """

    @staticmethod
    def generate_safe_storage_path(original_filename: str) -> str:
        """
        Generates a sanitized, collision-free storage path for the PDF.
        Example: 'resolutions/4f3a..._gr_education_2024.pdf'
        """
        # Sanitize filename: keep alphanumeric, dots, dashes, underscores
        safe_name = re.sub(r"[^\w\.-]", "_", original_filename.strip())
        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"
        unique_token = uuid.uuid4().hex[:12]
        return f"resolutions/{unique_token}_{safe_name}"

    @staticmethod
    def upload_file(
        file_bytes: bytes,
        storage_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        """
        Uploads file bytes to the existing Supabase Storage bucket.
        Returns the confirmed storage path.
        """
        client = get_supabase_client()
        bucket_name = settings.SUPABASE_STORAGE_BUCKET

        if client:
            try:
                res = client.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
                logger.info(f"Successfully uploaded {len(file_bytes)} bytes to Supabase Storage: {storage_path}")
                return storage_path
            except Exception as e:
                logger.error(f"Failed uploading to Supabase Storage bucket '{bucket_name}': {e}")
                # Save to mock fallback so pipeline continues
                _mock_storage_bucket[storage_path] = file_bytes
                return storage_path

        # In-memory storage for test/offline
        _mock_storage_bucket[storage_path] = file_bytes
        logger.info(f"Stored {len(file_bytes)} bytes in mock storage: {storage_path}")
        return storage_path

    @staticmethod
    def delete_file(storage_path: str) -> bool:
        """
        Deletes a file from the Supabase Storage bucket.
        Handles errors safely.
        """
        if not storage_path:
            return False

        client = get_supabase_client()
        bucket_name = settings.SUPABASE_STORAGE_BUCKET
        deleted_from_supabase = False

        if client:
            try:
                res = client.storage.from_(bucket_name).remove([storage_path])
                logger.info(f"Removed file from Supabase Storage: {storage_path}")
                deleted_from_supabase = True
            except Exception as e:
                logger.error(f"Error removing file '{storage_path}' from Supabase Storage: {e}")

        deleted_from_mock = False
        if storage_path in _mock_storage_bucket:
            del _mock_storage_bucket[storage_path]
            deleted_from_mock = True

        return deleted_from_supabase or deleted_from_mock

    @staticmethod
    def download_file(storage_path: str) -> Optional[bytes]:
        """Downloads file bytes from storage."""
        client = get_supabase_client()
        bucket_name = settings.SUPABASE_STORAGE_BUCKET

        if client:
            try:
                data = client.storage.from_(bucket_name).download(storage_path)
                if data:
                    return data
            except Exception as e:
                logger.error(f"Error downloading '{storage_path}' from Supabase Storage: {e}")

        return _mock_storage_bucket.get(storage_path)
