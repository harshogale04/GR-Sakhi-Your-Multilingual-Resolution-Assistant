from typing import List, Optional
from uuid import UUID
from backend.app.core.logging import logger
from backend.app.db.repositories.document_repository import DocumentRepository
from backend.app.db.repositories.chunk_repository import ChunkRepository
from backend.app.services.storage_service import StorageService
from backend.app.db.pinecone import get_pinecone_index
from backend.app.schemas.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    DocumentStatusResponse,
    PaginatedDocumentsResponse,
    DocumentDeleteResult,
    DocumentStatsResponse,
)


class DocumentService:
    """
    Business service layer orchestrating DocumentRepository, ChunkRepository,
    StorageService, and Pinecone vector cleanup.
    """

    @staticmethod
    def create_document(doc_in: DocumentCreate) -> DocumentResponse:
        return DocumentRepository.create(doc_in)

    @staticmethod
    def get_document_by_id(doc_id: UUID) -> Optional[DocumentResponse]:
        return DocumentRepository.get_by_id(doc_id)

    @staticmethod
    def get_status(doc_id: UUID) -> Optional[DocumentStatusResponse]:
        return DocumentRepository.get_status(doc_id)

    @staticmethod
    def get_documents_paginated(
        page: int = 1,
        limit: int = 20,
        department: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedDocumentsResponse:
        return DocumentRepository.list_paginated(
            page=page,
            limit=limit,
            department=department,
            language=language,
            status=status,
            search=search,
        )

    @staticmethod
    def get_documents(
        department: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[DocumentResponse]:
        """Convenience method returning unpaginated list (used by existing internal callers)."""
        res = DocumentRepository.list_paginated(
            page=1,
            limit=1000,
            department=department,
            language=language,
            status=status,
            search=search,
        )
        return res.items

    @staticmethod
    def update_document(doc_id: UUID, updates: DocumentUpdate) -> Optional[DocumentResponse]:
        return DocumentRepository.update(doc_id, updates)

    @staticmethod
    def delete_document_workflow(doc_id: UUID) -> DocumentDeleteResult:
        """
        Executes the safe document deletion workflow:
        1. Retrieve the document's storage path.
        2. Retrieve associated vector IDs from 'chunks'.
        3. Delete vectors from Pinecone when available.
        4. Delete original PDF from Supabase Storage.
        5. Delete the document record from 'documents'.
        6. Let the existing foreign key cascade remove chunk references.
        7. Handle partial failures carefully without crashing.
        """
        # 1. Retrieve document
        doc = DocumentRepository.get_by_id(doc_id)
        if not doc:
            return DocumentDeleteResult(
                success=False,
                document_id=doc_id,
                message="Document not found.",
            )

        storage_path = doc.storage_path

        # 2. Retrieve associated vector IDs from 'chunks'
        vector_ids = ChunkRepository.get_pinecone_ids_by_document(doc_id)
        chunks_count = len(vector_ids)

        # 3. Delete vectors from Pinecone when available
        vectors_deleted_count = 0
        try:
            from backend.app.services.vector_store_service import VectorStoreService
            vectors_deleted_count = VectorStoreService.delete_by_document_id(doc_id, vector_ids=vector_ids)
        except Exception as e:
            logger.warning(
                f"Notice: Failed to delete vectors from Pinecone for document {doc_id}: {e}. "
                f"Proceeding with database and storage cleanup."
            )

        # 4. Delete the original PDF from Supabase Storage
        storage_deleted = False
        try:
            if storage_path:
                storage_deleted = StorageService.delete_file(storage_path)
        except Exception as e:
            logger.error(f"Error deleting file '{storage_path}' from storage: {e}")

        # 5. Delete document record (foreign key cascade removes chunks in PostgreSQL)
        # Also clean up mock chunks if any
        ChunkRepository.delete_by_document(doc_id)
        doc_deleted = DocumentRepository.delete(doc_id)

        return DocumentDeleteResult(
            success=doc_deleted,
            document_id=doc_id,
            message="Document and associated assets deleted successfully.",
            storage_deleted=storage_deleted,
            vectors_deleted=vectors_deleted_count,
            chunks_removed=chunks_count,
        )

    @staticmethod
    def delete_document(doc_id: UUID) -> bool:
        """Backwards compatible deletion method."""
        result = DocumentService.delete_document_workflow(doc_id)
        return result.success

    @staticmethod
    def get_stats() -> DocumentStatsResponse:
        return DocumentRepository.get_stats()
