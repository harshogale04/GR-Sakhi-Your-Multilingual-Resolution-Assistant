from uuid import uuid4
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from backend.app.schemas.documents import DocumentCreate, DocumentResponse
from backend.app.schemas.chunks import ChunkCreate, ChunkResponse


def test_document_schema_strict_fields():
    """Verify document schema strictly conforms to Supabase 'documents' table."""
    doc_id = uuid4()
    now = datetime.now(timezone.utc)

    # Valid instantiation
    doc = DocumentResponse(
        id=doc_id,
        filename="test_file.pdf",
        original_filename="Original Test.pdf",
        storage_path="resolutions/test_file.pdf",
        status="PROCESSING",
        category="Policy",
        department="School Education",
        language="mr",
        document_type="Government Resolution",
        subject="शैक्षणिक धोरण नियमावली",
        gr_number="संकीर्ण-२०२४/१२",
        pages=5,
        chunk_count=12,
        uploaded_at=now,
    )
    assert doc.id == doc_id
    assert doc.status == "PROCESSING"

    # Verify no 'error_message' column in fields
    assert "error_message" not in DocumentResponse.model_fields
    assert "error_message" not in DocumentCreate.model_fields


def test_chunk_schema_strict_fields():
    """Verify chunk schema strictly conforms to Supabase 'chunks' table."""
    doc_id = uuid4()
    chunk_id = f"{doc_id}_chk_1"
    pinecone_id = f"vec_{chunk_id}"
    uuid_id = uuid4()
    now = datetime.now(timezone.utc)

    chunk = ChunkResponse(
        id=uuid_id,
        chunk_id=chunk_id,
        document_id=doc_id,
        page=1,
        section="प्रस्तावना",
        pinecone_id=pinecone_id,
        created_at=now,
    )
    assert chunk.document_id == doc_id
    assert chunk.page == 1

    # Verify NO 'text' column on chunks table
    assert "text" not in ChunkResponse.model_fields
    assert "text" not in ChunkCreate.model_fields


def test_search_and_chat_schemas():
    from backend.app.schemas.search import SearchQueryRequest, SearchResponse
    from backend.app.schemas.chat import ChatRequest, ChatResponse

    search_req = SearchQueryRequest(query="शेतकरी कर्जमाफी", language="mr", top_k=5)
    assert search_req.query == "शेतकरी कर्जमाफी"
    assert search_req.language == "mr"

    chat_req = ChatRequest(query="आरोग्य भरती नियम", language="mr")
    assert chat_req.query == "आरोग्य भरती नियम"


def test_stage2_document_schemas():
    """Verify Stage 2 additions: upload response, paginated, status, and delete result."""
    from backend.app.schemas.documents import (
        DocumentUploadResponse,
        DocumentStatusResponse,
        PaginatedDocumentsResponse,
        DocumentDeleteResult,
        DocumentStatsResponse,
    )

    doc_id = uuid4()
    now = datetime.now(timezone.utc)

    # 1. DocumentUploadResponse
    upload_resp = DocumentUploadResponse(
        id=doc_id,
        filename="test.pdf",
        original_filename="original.pdf",
        storage_path="resolutions/test.pdf",
        status="PROCESSING",
        message="Uploaded successfully",
    )
    assert upload_resp.id == doc_id
    assert upload_resp.status == "PROCESSING"

    # 2. DocumentStatusResponse
    status_resp = DocumentStatusResponse(
        id=doc_id,
        status="COMPLETED",
        pages=3,
        chunk_count=6,
        uploaded_at=now,
    )
    assert status_resp.status == "COMPLETED"

    # 3. PaginatedDocumentsResponse
    paginated = PaginatedDocumentsResponse(
        items=[],
        total=0,
        page=1,
        limit=20,
        pages=1,
    )
    assert paginated.total == 0
    assert paginated.items == []

    # 4. DocumentDeleteResult
    del_result = DocumentDeleteResult(
        success=True,
        document_id=doc_id,
        message="Deleted",
        storage_deleted=True,
        vectors_deleted=5,
        chunks_removed=5,
    )
    assert del_result.success is True

    # 5. DocumentStatsResponse
    stats = DocumentStatsResponse(
        total_documents=10,
        total_chunks=50,
        completed_documents=8,
        indexed_documents=8,
        processing_documents=1,
        failed_documents=1,
        departments_count=4,
        language_breakdown={"mr": 8, "hi": 1, "en": 1},
    )
    assert stats.completed_documents == 8
    assert stats.failed_documents == 1

