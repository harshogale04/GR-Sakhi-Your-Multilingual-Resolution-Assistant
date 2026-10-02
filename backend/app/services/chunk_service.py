from typing import List
from uuid import UUID
from backend.app.db.repositories.chunk_repository import ChunkRepository
from backend.app.schemas.chunks import ChunkCreate, ChunkResponse


class ChunkService:
    """Service layer delegating to ChunkRepository."""

    @staticmethod
    def create_chunk(chunk_in: ChunkCreate) -> ChunkResponse:
        return ChunkRepository.create(chunk_in)

    @staticmethod
    def create_chunks_batch(chunks_in: List[ChunkCreate]) -> List[ChunkResponse]:
        return ChunkRepository.create_batch(chunks_in)

    @staticmethod
    def get_chunks_by_document(document_id: UUID) -> List[ChunkResponse]:
        return ChunkRepository.get_by_document(document_id)

    @staticmethod
    def get_pinecone_ids_by_document(document_id: UUID) -> List[str]:
        return ChunkRepository.get_pinecone_ids_by_document(document_id)

    @staticmethod
    def delete_chunks_by_document(document_id: UUID) -> int:
        return ChunkRepository.delete_by_document(document_id)
