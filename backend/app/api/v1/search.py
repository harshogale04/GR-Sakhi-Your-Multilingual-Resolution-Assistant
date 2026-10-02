from fastapi import APIRouter
from backend.app.schemas.search import SearchQueryRequest, SearchResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_resolutions(query_req: SearchQueryRequest):
    """
    Multilingual semantic search across indexed Maharashtra Government Resolutions:
    - Generates query embedding with gemini-embedding-001.
    - Searches Pinecone vector database.
    - Hydrates document details from Supabase.
    - Returns ranked matching passages with cosine scores.
    """
    return RAGService.search_semantic(
        query=query_req.query,
        language=query_req.language or "mr",
        department=query_req.department,
        top_k=query_req.top_k or 10,
    )
