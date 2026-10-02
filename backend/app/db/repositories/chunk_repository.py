from datetime import datetime, timezone
from typing import List, Dict
from uuid import UUID, uuid4
from backend.app.core.logging import logger
from backend.app.db.supabase import get_supabase_client
from backend.app.schemas.chunks import ChunkCreate, ChunkResponse

_mock_chunks: Dict[str, dict] = {}


class ChunkRepository:
    """
    Dedicated repository for the Supabase 'chunks' table.
    Strictly conforms to the 7 columns of the existing table:
    id, chunk_id, document_id, page, section, pinecone_id, created_at.
    Note: Chunk text is stored in Pinecone metadata, NOT in the database.
    """

    @staticmethod
    def create(chunk_in: ChunkCreate) -> ChunkResponse:
        client = get_supabase_client()
        data = {
            "chunk_id": chunk_in.chunk_id,
            "document_id": str(chunk_in.document_id),
            "page": chunk_in.page,
            "section": chunk_in.section,
            "pinecone_id": chunk_in.pinecone_id,
        }

        if client:
            try:
                res = client.table("chunks").insert(data).execute()
                if res.data and len(res.data) > 0:
                    return ChunkResponse(**res.data[0])
            except Exception as e:
                logger.error(f"Database error inserting chunk into Supabase: {e}")

        # Local fallback
        c_id = uuid4()
        now = datetime.now(timezone.utc)
        record = {
            "id": c_id,
            "created_at": now,
            **data,
            "document_id": chunk_in.document_id,
        }
        _mock_chunks[str(c_id)] = record
        return ChunkResponse(**record)

    @staticmethod
    def create_batch(chunks_in: List[ChunkCreate]) -> List[ChunkResponse]:
        if not chunks_in:
            return []

        client = get_supabase_client()
        data_list = [
            {
                "chunk_id": c.chunk_id,
                "document_id": str(c.document_id),
                "page": c.page,
                "section": c.section,
                "pinecone_id": c.pinecone_id,
            }
            for c in chunks_in
        ]

        if client:
            try:
                res = client.table("chunks").insert(data_list).execute()
                if res.data:
                    logger.info(f"Batch inserted {len(res.data)} chunks into Supabase.")
                    return [ChunkResponse(**row) for row in res.data]
            except Exception as e:
                logger.error(f"Database error batch inserting chunks into Supabase: {e}")

        # Fallback to local store
        created = []
        now = datetime.now(timezone.utc)
        for c, d in zip(chunks_in, data_list):
            c_id = uuid4()
            record = {
                "id": c_id,
                "created_at": now,
                **d,
                "document_id": c.document_id,
            }
            _mock_chunks[str(c_id)] = record
            created.append(ChunkResponse(**record))
        return created

    @staticmethod
    def get_by_document(document_id: UUID) -> List[ChunkResponse]:
        client = get_supabase_client()
        if client:
            try:
                res = (
                    client.table("chunks")
                    .select("*")
                    .eq("document_id", str(document_id))
                    .order("page", desc=False)
                    .execute()
                )
                if res.data:
                    return [ChunkResponse(**row) for row in res.data]
            except Exception as e:
                logger.error(f"Database error fetching chunks for document {document_id}: {e}")

        results = [
            ChunkResponse(**row)
            for row in _mock_chunks.values()
            if str(row["document_id"]) == str(document_id)
        ]
        return sorted(results, key=lambda x: (x.page or 0))

    @staticmethod
    def get_pinecone_ids_by_document(document_id: UUID) -> List[str]:
        """Retrieves vector IDs to delete from Pinecone before cascade removing chunks."""
        chunks = ChunkRepository.get_by_document(document_id)
        return [c.pinecone_id for c in chunks if c.pinecone_id]

    @staticmethod
    def delete_by_document(document_id: UUID) -> int:
        """
        Explicitly removes chunks for a document.
        Note: The PostgreSQL foreign key constraint 'chunks_document_id_fkey'
        already includes ON DELETE CASCADE, but this provides safe repository-level deletion.
        """
        count = 0
        client = get_supabase_client()
        if client:
            try:
                res = client.table("chunks").delete().eq("document_id", str(document_id)).execute()
                count = len(res.data) if res.data else 0
            except Exception as e:
                logger.error(f"Database error deleting chunks for document {document_id}: {e}")

        to_remove = [k for k, v in _mock_chunks.items() if str(v["document_id"]) == str(document_id)]
        for k in to_remove:
            del _mock_chunks[k]
        return count or len(to_remove)
