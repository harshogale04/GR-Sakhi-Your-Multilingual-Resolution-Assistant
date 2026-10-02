from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from backend.app.schemas.documents import DocumentResponse


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search text in Marathi, Hindi, or English")
    language: Optional[str] = Field(default="mr", description="Query language code (mr, hi, en)")
    top_k: Optional[int] = Field(default=10, ge=1, le=50, description="Max passages to retrieve")
    department: Optional[str] = Field(default=None, description="Filter by department")
    category: Optional[str] = Field(default=None, description="Filter by category")


class SearchResultItem(BaseModel):
    chunk_id: str
    pinecone_id: str
    document_id: UUID
    score: float
    text: str  # Extracted from Pinecone vector metadata
    page: Optional[int] = None
    section: Optional[str] = None
    document: Optional[DocumentResponse] = None


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    language: str
