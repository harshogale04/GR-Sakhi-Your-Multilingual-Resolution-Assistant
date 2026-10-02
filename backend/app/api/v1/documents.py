from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from backend.app.core.logging import logger
from backend.app.schemas.documents import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentStatusResponse,
    PaginatedDocumentsResponse,
    DocumentDeleteResult,
    DocumentStatsResponse,
)
from backend.app.schemas.chunks import ChunkResponse
from backend.app.services.document_service import DocumentService
from backend.app.services.chunk_service import ChunkService
from backend.app.services.storage_service import StorageService
from backend.app.services.rag_service import RAGService
from backend.app.schemas.documents import DocumentCreate

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

router = APIRouter(prefix="/documents", tags=["Documents"])


# ------------------------------------------------------------------
# Upload  (POST /documents/upload)
# ------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a Maharashtra Government Resolution PDF",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document of the Government Resolution"),
    department: Optional[str] = Form("School Education"),
    gr_number: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    category: Optional[str] = Form("Policy"),
    language: Optional[str] = Form("mr"),
    document_type: Optional[str] = Form("Government Resolution"),
):
    """
    Upload a PDF and return immediately after registration.

    Processing runs in the background:
    1. Validate PDF format and file size.
    2. Generate a safe, unique storage path.
    3. Upload PDF to Supabase Storage.
    4. Register document record (status: PROCESSING).
    5. Trigger background extraction → embedding → Pinecone → chunks.
    6. Return document ID and current status immediately.
    """
    # --- Validation ---
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF (.pdf) documents are accepted.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 50 MB.",
        )

    logger.info(f"Upload received: '{file.filename}' ({len(file_bytes):,} bytes)")

    # --- Upload to storage ---
    storage_path = StorageService.generate_safe_storage_path(file.filename)
    try:
        StorageService.upload_file(file_bytes, storage_path)
    except Exception as e:
        logger.error(f"Storage upload failed for '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document to storage. Please try again.",
        )

    # --- Register document in DB with PROCESSING status ---
    doc_in = DocumentCreate(
        filename=storage_path.split("/")[-1],
        original_filename=file.filename,
        storage_path=storage_path,
        status="PROCESSING",
        category=category,
        department=department,
        language=language or "mr",
        document_type=document_type,
        subject=subject or file.filename,
        gr_number=gr_number or None,
    )
    created_doc = DocumentService.create_document(doc_in)

    # --- Queue background processing ---
    background_tasks.add_task(
        RAGService.process_document_background,
        doc_id=created_doc.id,
        file_bytes=file_bytes,
        original_filename=file.filename,
        subject=subject,
        gr_number=gr_number,
        department=department,
        language=language,
    )

    logger.info(f"Document {created_doc.id} registered; background processing queued.")

    return DocumentUploadResponse(
        id=created_doc.id,
        filename=created_doc.filename,
        original_filename=created_doc.original_filename,
        storage_path=created_doc.storage_path,
        status=created_doc.status,
        message="Document uploaded successfully. Text extraction, embedding, and indexing are running in the background.",
    )


# ------------------------------------------------------------------
# List Documents  (GET /documents)
# ------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedDocumentsResponse,
    summary="List Government Resolution documents (paginated)",
)
def list_documents(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    language: Optional[str] = Query(None, description="Filter by language (mr, hi, en)"),
    status: Optional[str] = Query(None, description="Filter by status: PROCESSING, COMPLETED, FAILED"),
    search: Optional[str] = Query(None, description="Full-text search on subject, filename, gr_number"),
):
    """Return a paginated list of Government Resolution records with optional filters."""
    return DocumentService.get_documents_paginated(
        page=page,
        limit=limit,
        department=department,
        language=language,
        status=status,
        search=search,
    )


# ------------------------------------------------------------------
# Stats  (GET /documents/stats)
# ------------------------------------------------------------------

@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
    summary="Get statistical breakdown of the GR repository",
)
def get_document_statistics():
    """Retrieve aggregated statistics: totals, status counts, department count, language breakdown."""
    return DocumentService.get_stats()


# ------------------------------------------------------------------
# Single Document  (GET /documents/{doc_id})
# ------------------------------------------------------------------

@router.get(
    "/{doc_id}",
    response_model=DocumentResponse,
    summary="Get a single Government Resolution document by ID",
)
def get_document(doc_id: UUID):
    """Retrieve a single GR document record by its UUID."""
    doc = DocumentService.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Government Resolution not found.")
    return doc


# ------------------------------------------------------------------
# Status Polling  (GET /documents/{doc_id}/status)
# ------------------------------------------------------------------

@router.get(
    "/{doc_id}/status",
    response_model=DocumentStatusResponse,
    summary="Poll processing status of an uploaded document",
)
def get_document_status(doc_id: UUID):
    """
    Lightweight endpoint for polling document status after upload.
    Returns PROCESSING, COMPLETED, or FAILED with optional page/chunk counts.
    """
    doc_status = DocumentService.get_status(doc_id)
    if not doc_status:
        raise HTTPException(status_code=404, detail="Government Resolution not found.")
    return doc_status


# ------------------------------------------------------------------
# Chunk Registry  (GET /documents/{doc_id}/chunks)
# ------------------------------------------------------------------

@router.get(
    "/{doc_id}/chunks",
    response_model=List[ChunkResponse],
    summary="Retrieve relational chunk registry entries for a document",
)
def get_document_chunks(doc_id: UUID):
    """
    Returns the relational chunk entries from the Supabase 'chunks' table.
    These are lightweight registry records; full chunk text lives in Pinecone metadata.
    """
    doc = DocumentService.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Government Resolution not found.")
    return ChunkService.get_chunks_by_document(doc_id)


# ------------------------------------------------------------------
# Delete  (DELETE /documents/{doc_id})
# ------------------------------------------------------------------

@router.delete(
    "/{doc_id}",
    response_model=DocumentDeleteResult,
    summary="Delete a Government Resolution and all associated assets",
)
def delete_document(doc_id: UUID):
    """
    Execute the safe document deletion workflow:
    1. Retrieve associated Pinecone vector IDs from 'chunks'.
    2. Delete vectors from Pinecone (non-blocking on error).
    3. Delete original PDF from Supabase Storage.
    4. Delete document record (FK cascade removes chunks).
    """
    result = DocumentService.delete_document_workflow(doc_id)
    if not result.success and result.message == "Document not found.":
        raise HTTPException(status_code=404, detail="Government Resolution not found.")
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.message,
        )
    return result


# ------------------------------------------------------------------
# Download / Preview PDF  (GET /documents/{doc_id}/download)
# ------------------------------------------------------------------

@router.get(
    "/{doc_id}/download",
    summary="Download or stream the original Government Resolution PDF",
)
def download_document(doc_id: UUID):
    """
    Retrieves the original PDF file from Supabase Storage (or mock storage fallback)
    and streams it with application/pdf content type for inline viewing or download.
    """
    doc = DocumentService.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Government Resolution not found.")

    file_bytes = StorageService.download_file(doc.storage_path)
    if not file_bytes:
        raise HTTPException(
            status_code=404,
            detail="The original PDF file was not found in storage.",
        )

    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{doc.original_filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )

