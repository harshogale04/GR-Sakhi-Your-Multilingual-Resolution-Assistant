"""
Pinecone Vector Store Service for MAHA-GR.
Handles:
- Index dimension and connectivity validation.
- Vector upsert with compliant Pinecone metadata types.
- Semantic query with metadata filtering (department, language, document_id).
- Vector deletion by document ID.
- In-memory fallback vector store for local testing without external Pinecone credentials.
"""
import math
from typing import List, Dict, Any, Optional
from uuid import UUID
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.pinecone import get_pinecone_index, check_pinecone_connection
from backend.app.services.embedding_service import EmbeddingService, EMBEDDING_DIMENSION

# Module-level mock store for local development / test execution
_mock_pinecone_store: Dict[str, Dict[str, Any]] = {}


class VectorStoreService:
    @classmethod
    def upsert_chunks(
        cls,
        vectors: List[Dict[str, Any]],
    ) -> int:
        """
        Upserts chunk vectors and compliant metadata into Pinecone.
        Each item in `vectors` must have:
            id: str (identical to chunks.pinecone_id)
            values: List[float] (768-dim embedding)
            metadata: Dict[str, Any]
        """
        if not vectors:
            return 0

        # Sanitize metadata: Pinecone supports string, number, boolean, or list of strings.
        # Null values must be omitted.
        sanitized_vectors = []
        for v in vectors:
            raw_meta = v.get("metadata", {})
            clean_meta = {}
            for k, val in raw_meta.items():
                if val is not None:
                    if isinstance(val, (str, int, float, bool)):
                        clean_meta[k] = val
                    elif isinstance(val, list) and all(isinstance(x, str) for x in val):
                        clean_meta[k] = val
                    else:
                        clean_meta[k] = str(val)

            sanitized_vectors.append({
                "id": v["id"],
                "values": v["values"],
                "metadata": clean_meta,
            })

            # Also maintain in local mock store
            _mock_pinecone_store[v["id"]] = {
                "id": v["id"],
                "values": v["values"],
                "metadata": clean_meta,
            }

        pinecone_idx = get_pinecone_index()
        if pinecone_idx:
            try:
                # Check dimension compatibility
                EmbeddingService.validate_pinecone_index_dimension(pinecone_idx)

                # Batch upsert in chunks of 50
                batch_size = 50
                for i in range(0, len(sanitized_vectors), batch_size):
                    batch = sanitized_vectors[i:i + batch_size]
                    pinecone_idx.upsert(vectors=batch)

                logger.info(f"Upserted {len(sanitized_vectors)} vectors into Pinecone.")
                return len(sanitized_vectors)
            except Exception as e:
                logger.error(f"Error upserting vectors to Pinecone: {e}. Kept in memory mock.")

        return len(sanitized_vectors)

    @classmethod
    def query_similar(
        cls,
        query_vector: List[float],
        top_k: int = 10,
        department: Optional[str] = None,
        language: Optional[str] = None,
        document_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity query against Pinecone (or fallback in-memory store).
        Returns list of matching dicts:
            [{"id": str, "score": float, "metadata": dict}]
        """
        results: List[Dict[str, Any]] = []

        # Construct metadata filter
        filter_dict: Dict[str, Any] = {}
        if department and department != "all":
            filter_dict["department"] = {"$eq": department}
        if language:
            filter_dict["language"] = {"$eq": language}
        if document_id:
            filter_dict["document_id"] = {"$eq": str(document_id)}

        pinecone_idx = get_pinecone_index()
        if pinecone_idx:
            try:
                query_args = {
                    "vector": query_vector,
                    "top_k": top_k,
                    "include_metadata": True,
                }
                if filter_dict:
                    query_args["filter"] = filter_dict

                res = pinecone_idx.query(**query_args)
                for match in res.get("matches", []):
                    results.append({
                        "id": match.get("id"),
                        "score": float(match.get("score", 0.0)),
                        "metadata": match.get("metadata", {}),
                    })
                if results:
                    return results
            except Exception as e:
                logger.error(f"Pinecone query error: {e}. Falling back to in-memory search.")

        # Local in-memory cosine similarity fallback
        if _mock_pinecone_store:
            scored = []
            for item in _mock_pinecone_store.values():
                meta = item.get("metadata", {})
                if department and department != "all" and meta.get("department") != department:
                    continue
                if language and meta.get("language") != language:
                    continue
                if document_id and meta.get("document_id") != str(document_id):
                    continue

                sim = cls._cosine_similarity(query_vector, item["values"])
                scored.append((sim, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            for score, item in scored[:top_k]:
                results.append({
                    "id": item["id"],
                    "score": round(float(score), 4),
                    "metadata": item["metadata"],
                })

        return results

    @classmethod
    def delete_by_document_id(cls, document_id: UUID, vector_ids: Optional[List[str]] = None) -> int:
        """Deletes all vector embeddings associated with a document_id."""
        doc_id_str = str(document_id)
        deleted_count = 0

        # Remove from local mock store
        to_del = [k for k, v in _mock_pinecone_store.items() if v.get("metadata", {}).get("document_id") == doc_id_str]
        for k in to_del:
            del _mock_pinecone_store[k]
            deleted_count += 1

        pinecone_idx = get_pinecone_index()
        if pinecone_idx:
            # Prioritize deleting by explicit ID list (compatible with all Pinecone index tiers)
            target_ids = list(set((vector_ids or []) + to_del))
            if target_ids:
                try:
                    pinecone_idx.delete(ids=target_ids)
                    logger.info(f"Deleted {len(target_ids)} vectors by IDs for document {doc_id_str} from Pinecone.")
                    return max(deleted_count, len(target_ids))
                except Exception as e:
                    logger.warning(f"Could not delete Pinecone vectors by IDs: {e}. Trying filter.")

            # Fallback to metadata filter delete
            try:
                pinecone_idx.delete(filter={"document_id": {"$eq": doc_id_str}})
                logger.info(f"Deleted vectors for document {doc_id_str} from Pinecone by filter.")
            except Exception as e:
                logger.error(f"Failed to delete Pinecone vectors by filter: {e}")

        return deleted_count

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        if not mag1 or not mag2:
            return 0.0
        return max(-1.0, min(1.0, dot / (mag1 * mag2)))
