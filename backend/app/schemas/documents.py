from datetime import datetime
from typing import Optional, Dict, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

# Canonical status values strictly requested:
# 'PROCESSING', 'COMPLETED', 'FAILED' (with 'INDEXED' supported for backwards compatibility)
DocumentStatusType = Literal["PROCESSING", "COMPLETED", "FAILED", "INDEXED"]


class DocumentBase(BaseModel):
    """
    Base schema strictly adhering to existing Supabase 'documents' table.
    Columns:
    - id
    - filename
    - original_filename
    - storage_path
    - status ('PROCESSING', 'COMPLETED', 'FAILED')
    - category
    - department
    - language
    - document_type
    - subject
    - gr_number
    - pages
    - chunk_count
    - uploaded_at
    """
    filename: str
    original_filename: str
    storage_path: str
    status: str = Field(default="PROCESSING")
    category: Optional[str] = None
    department: Optional[str] = None
    language: Optional[str] = "mr"
    document_type: Optional[str] = "Government Resolution"
    subject: Optional[str] = None
    gr_number: Optional[str] = None
    pages: Optional[int] = None
    chunk_count: Optional[int] = None


class DocumentCreate(DocumentBase):
    """Schema for inserting a new document record into 'documents'."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating document status and counts (only allowed fields)."""
    status: Optional[str] = None
    pages: Optional[int] = None
    chunk_count: Optional[int] = None
    subject: Optional[str] = None
    gr_number: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    language: Optional[str] = None
    document_type: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema representing complete document returned from 'documents' table."""
    id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    """Immediate response after upload before background processing finishes."""
    id: UUID
    filename: str
    original_filename: str
    storage_path: str
    status: str = "PROCESSING"
    message: str = "Document uploaded successfully. Processing started in background."


class DocumentStatusResponse(BaseModel):
    """Lightweight response for status polling."""
    id: UUID
    status: str
    pages: Optional[int] = None
    chunk_count: Optional[int] = None
    uploaded_at: datetime


class PaginatedDocumentsResponse(BaseModel):
    """Structured paginated list of documents."""
    items: List[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int


class DocumentDeleteResult(BaseModel):
    """Structured response for document deletion workflow."""
    success: bool
    document_id: UUID
    message: str
    storage_deleted: bool = False
    vectors_deleted: int = 0
    chunks_removed: int = 0


class DocumentStatsResponse(BaseModel):
    """Aggregated stats derived from documents and chunks."""
    total_documents: int
    total_chunks: int
    completed_documents: int
    indexed_documents: int  # Aliased to completed for backwards compatibility
    processing_documents: int
    failed_documents: int
    departments_count: int
    language_breakdown: Dict[str, int]
