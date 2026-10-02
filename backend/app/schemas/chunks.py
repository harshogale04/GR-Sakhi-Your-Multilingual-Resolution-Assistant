from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ChunkBase(BaseModel):
    """
    Base schema strictly adhering to existing Supabase 'chunks' table.
    Note: The chunks table is a relational registry.
    Actual chunk text is stored in Pinecone metadata.
    """
    chunk_id: str
    document_id: UUID
    page: Optional[int] = None
    section: Optional[str] = None
    pinecone_id: str


class ChunkCreate(ChunkBase):
    """Schema for inserting a new chunk mapping into 'chunks'."""
    pass


class ChunkResponse(ChunkBase):
    """Schema representing complete chunk record from 'chunks' table."""
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
