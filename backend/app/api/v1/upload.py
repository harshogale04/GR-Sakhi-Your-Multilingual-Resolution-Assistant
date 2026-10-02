"""
Legacy /upload endpoint — kept for backwards compatibility.
New code should use POST /api/v1/documents/upload instead.

This thin wrapper delegates directly to the documents upload handler.
"""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from backend.app.schemas.documents import DocumentUploadResponse, DocumentCreate
from backend.app.services.document_service import DocumentService
from backend.app.services.storage_service import StorageService
from backend.app.services.rag_service import RAGService
from backend.app.core.logging import logger

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

router = APIRouter(prefix="/upload", tags=["Upload (Legacy)"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Legacy] Upload a Government Resolution PDF — prefer /documents/upload",
)
async def upload_government_resolution_legacy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document of Government Resolution"),
    department: Optional[str] = Form("School Education"),
    gr_number: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    category: Optional[str] = Form("Policy"),
    language: Optional[str] = Form("mr"),
    document_type: Optional[str] = Form("Government Resolution"),
):
    """
    Backwards-compatible upload endpoint.
    Delegates to the same pipeline as POST /documents/upload.
    """
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
            detail="File exceeds maximum allowed size of 50 MB.",
        )

    logger.info(f"[Legacy /upload] Received '{file.filename}' ({len(file_bytes):,} bytes)")

    storage_path = StorageService.generate_safe_storage_path(file.filename)
    try:
        StorageService.upload_file(file_bytes, storage_path)
    except Exception as e:
        logger.error(f"[Legacy /upload] Storage upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document to storage.",
        )

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

    return DocumentUploadResponse(
        id=created_doc.id,
        filename=created_doc.filename,
        original_filename=created_doc.original_filename,
        storage_path=created_doc.storage_path,
        status=created_doc.status,
        message="Document uploaded successfully. Processing started in background.",
    )
