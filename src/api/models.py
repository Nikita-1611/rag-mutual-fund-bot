from pydantic import BaseModel
from typing import Optional, Dict, Any

class SessionInitResponse(BaseModel):
    session_id: str

class ChatQueryRequest(BaseModel):
    session_id: str
    query: str

class ChatQueryResponse(BaseModel):
    answer: str
    source_url: str
    last_updated: str
    is_refusal: Optional[bool] = False

class IngestResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    pinecone_connected: bool
    gemini_connected: bool
    cohere_connected: bool
    pinecone_latency_ms: Optional[float] = 0.0
    gemini_latency_ms: Optional[float] = 0.0
    cohere_latency_ms: Optional[float] = 0.0
