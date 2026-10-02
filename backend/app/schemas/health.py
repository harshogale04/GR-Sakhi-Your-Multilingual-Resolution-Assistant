from datetime import datetime
from pydantic import BaseModel


class ServiceHealthStatus(BaseModel):
    supabase_db: bool = False
    supabase_storage: bool = False
    pinecone: bool = False
    gemini_api: bool = False


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    environment: str
    is_demo_mode: bool = False
    timestamp: datetime
    services: ServiceHealthStatus

