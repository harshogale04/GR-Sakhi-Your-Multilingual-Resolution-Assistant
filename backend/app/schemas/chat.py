from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class ChatCitation(BaseModel):
    document_id: UUID
    document_title: str
    gr_number: Optional[str] = None
    department: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    snippet: str
    score: float


class ChatHistoryItem(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question asked by user in MR, HI, or EN")
    language: str = Field(default="mr", description="Target response language ('mr', 'hi', 'en')")
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    department: Optional[str] = None


class ChatMessageSchema(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    answer: Optional[str] = None
    language: str = "mr"
    insufficient_evidence: bool = False
    citations: List[ChatCitation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def sync_content_and_answer(cls, data: dict):
        if isinstance(data, dict):
            # Keep content and answer in sync for full API compatibility
            if "answer" in data and "content" not in data:
                data["content"] = data["answer"]
            elif "content" in data and "answer" not in data:
                data["answer"] = data["content"]
        return data


class ChatResponse(ChatMessageSchema):
    pass
