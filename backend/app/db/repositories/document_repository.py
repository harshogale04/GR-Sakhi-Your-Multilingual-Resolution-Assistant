import math
from datetime import datetime, timezone
from typing import Optional, Dict, List
from uuid import UUID, uuid4
from backend.app.core.logging import logger
from backend.app.db.supabase import get_supabase_client
from backend.app.schemas.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    DocumentStatusResponse,
    PaginatedDocumentsResponse,
    DocumentStatsResponse,
)

# In-memory storage cache used for development and test execution when credentials are not present
_mock_documents: Dict[str, dict] = {}


class DocumentRepository:
    """
    Dedicated repository for the Supabase 'documents' table.
    Strictly conforms to the 14 columns of the existing table:
    id, filename, original_filename, storage_path, status, category,
    department, language, document_type, subject, gr_number, pages,
    chunk_count, uploaded_at.
    """

    @staticmethod
    def create(doc_in: DocumentCreate) -> DocumentResponse:
        client = get_supabase_client()
        data = {
            "filename": doc_in.filename,
            "original_filename": doc_in.original_filename,
            "storage_path": doc_in.storage_path,
            "status": doc_in.status,
            "category": doc_in.category,
            "department": doc_in.department,
            "language": doc_in.language,
            "document_type": doc_in.document_type,
            "subject": doc_in.subject,
            "gr_number": doc_in.gr_number,
            "pages": doc_in.pages,
            "chunk_count": doc_in.chunk_count,
        }

        if client:
            try:
                res = client.table("documents").insert(data).execute()
                if res.data and len(res.data) > 0:
                    logger.info(f"Inserted document record into Supabase: {res.data[0]['id']}")
                    return DocumentResponse(**res.data[0])
            except Exception as e:
                logger.error(f"Database error inserting document into Supabase: {e}")

        # Local fallback
        doc_id = uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": doc_id,
            "uploaded_at": now,
            **data,
        }
        _mock_documents[str(doc_id)] = record
        logger.info(f"Stored document in memory cache: {doc_id}")
        return DocumentResponse(**record)

    @staticmethod
    def get_by_id(doc_id: UUID) -> Optional[DocumentResponse]:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("documents").select("*").eq("id", str(doc_id)).execute()
                if res.data and len(res.data) > 0:
                    return DocumentResponse(**res.data[0])
            except Exception as e:
                logger.error(f"Database error fetching document {doc_id} from Supabase: {e}")

        mock_data = _mock_documents.get(str(doc_id))
        return DocumentResponse(**mock_data) if mock_data else None

    @staticmethod
    def get_status(doc_id: UUID) -> Optional[DocumentStatusResponse]:
        doc = DocumentRepository.get_by_id(doc_id)
        if not doc:
            return None
        return DocumentStatusResponse(
            id=doc.id,
            status=doc.status,
            pages=doc.pages,
            chunk_count=doc.chunk_count,
            uploaded_at=doc.uploaded_at,
        )

    @staticmethod
    def list_paginated(
        page: int = 1,
        limit: int = 20,
        department: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedDocumentsResponse:
        page = max(1, page)
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit

        client = get_supabase_client()
        if client:
            try:
                query = client.table("documents").select("*", count="exact")

                if department and department != "all":
                    query = query.ilike("department", f"%{department}%")
                if language and language != "all":
                    query = query.eq("language", language)
                if status and status != "all":
                    query = query.eq("status", status)
                if search:
                    # Support searching by filename, original_filename, subject, or gr_number
                    query = query.or_(
                        f"filename.ilike.%{search}%,original_filename.ilike.%{search}%,subject.ilike.%{search}%,gr_number.ilike.%{search}%"
                    )

                res = query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()

                items = [DocumentResponse(**row) for row in (res.data or [])]
                total = res.count if res.count is not None else len(items)
                total_pages = math.ceil(total / limit) if total > 0 else 1

                return PaginatedDocumentsResponse(
                    items=items,
                    total=total,
                    page=page,
                    limit=limit,
                    pages=total_pages,
                )
            except Exception as e:
                logger.error(f"Database error listing documents from Supabase: {e}")

        # Fallback to local memory repository
        all_docs = [DocumentResponse(**item) for item in _mock_documents.values()]

        # Apply filters
        if department and department != "all":
            all_docs = [d for d in all_docs if d.department and department.lower() in d.department.lower()]
        if language and language != "all":
            all_docs = [d for d in all_docs if d.language == language]
        if status and status != "all":
            all_docs = [d for d in all_docs if d.status == status]
        if search:
            s_lower = search.lower()
            all_docs = [
                d for d in all_docs
                if (d.filename and s_lower in d.filename.lower())
                or (d.original_filename and s_lower in d.original_filename.lower())
                or (d.subject and s_lower in d.subject.lower())
                or (d.gr_number and s_lower in d.gr_number.lower())
            ]

        # Sort desc
        all_docs.sort(key=lambda x: x.uploaded_at, reverse=True)

        total = len(all_docs)
        total_pages = math.ceil(total / limit) if total > 0 else 1
        items = all_docs[offset : offset + limit]

        return PaginatedDocumentsResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=total_pages,
        )

    @staticmethod
    def update(doc_id: UUID, updates: DocumentUpdate) -> Optional[DocumentResponse]:
        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            return DocumentRepository.get_by_id(doc_id)

        client = get_supabase_client()
        if client:
            try:
                res = (
                    client.table("documents")
                    .update(update_dict)
                    .eq("id", str(doc_id))
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    return DocumentResponse(**res.data[0])
            except Exception as e:
                logger.error(f"Database error updating document {doc_id} in Supabase: {e}")

        if str(doc_id) in _mock_documents:
            _mock_documents[str(doc_id)].update(update_dict)
            return DocumentResponse(**_mock_documents[str(doc_id)])
        return None

    @staticmethod
    def delete(doc_id: UUID) -> bool:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("documents").delete().eq("id", str(doc_id)).execute()
                logger.info(f"Deleted document {doc_id} from Supabase.")
            except Exception as e:
                logger.error(f"Database error deleting document {doc_id} from Supabase: {e}")

        if str(doc_id) in _mock_documents:
            del _mock_documents[str(doc_id)]
        return True

    @staticmethod
    def get_stats() -> DocumentStatsResponse:
        docs = [DocumentResponse(**item) for item in _mock_documents.values()]
        client = get_supabase_client()
        if client:
            try:
                res = client.table("documents").select("*").execute()
                if res.data:
                    docs = [DocumentResponse(**row) for row in res.data]
            except Exception as e:
                logger.error(f"Database error retrieving stats from Supabase: {e}")

        total_docs = len(docs)
        total_chunks = sum(d.chunk_count or 0 for d in docs)
        completed_docs = sum(1 for d in docs if d.status in ("COMPLETED", "INDEXED"))
        processing_docs = sum(1 for d in docs if d.status == "PROCESSING")
        failed_docs = sum(1 for d in docs if d.status == "FAILED")

        departments = set(d.department for d in docs if d.department)
        lang_counts: Dict[str, int] = {}
        for d in docs:
            lang = d.language or "mr"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        return DocumentStatsResponse(
            total_documents=total_docs,
            total_chunks=total_chunks,
            completed_documents=completed_docs,
            indexed_documents=completed_docs,
            processing_documents=processing_docs,
            failed_documents=failed_docs,
            departments_count=len(departments),
            language_breakdown=lang_counts,
        )
