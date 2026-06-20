from typing import List, Optional

from pydantic import BaseModel


class ChunkRequest(BaseModel):
    text: str
    source: Optional[str] = "unknown"
    has_articles: Optional[bool] = None  # None = auto-detect


class ChunkResponse(BaseModel):
    chunks: List["DocumentChunk"]


class DocumentChunk(BaseModel):
    id: str
    article: str
    content: str
    source: str


DocumentChunk.model_rebuild()
