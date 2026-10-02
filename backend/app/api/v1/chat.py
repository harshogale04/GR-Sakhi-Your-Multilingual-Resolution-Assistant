from fastapi import APIRouter
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["AI Chat / RAG"])


@router.post("/ask", response_model=ChatResponse, summary="Grounded Conversational AI Q&A")
@router.post("", response_model=ChatResponse, summary="Alias for Grounded Conversational AI Q&A")
def ask_ai(chat_req: ChatRequest):
    """
    Grounded Conversational RAG with Gemini Flash:
    - Accepts user query in Marathi, Hindi, or English.
    - Searches source documents in Pinecone vector index.
    - Verifies evidence sufficiency.
    - Generates strictly grounded, evidence-based response.
    - Returns structured citations to original document and page.
    """
    history_dicts = (
        [{"role": h.role, "content": h.content} for h in chat_req.history]
        if chat_req.history
        else []
    )

    return RAGService.answer_query(
        query=chat_req.query,
        language=chat_req.language or "mr",
        history=history_dicts,
        department=chat_req.department,
        top_k=chat_req.top_k or 5,
    )
