from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RetrievalRequest(BaseModel):
    vector: List[float]
    limit: Optional[int] = 5
    filtros: Optional[Dict[str, Any]] = None


class ChunkResult(BaseModel):
    content: str
    source: str
    article: str
    norm_code: Optional[str] = None
    document_title: Optional[str] = None
    filename: Optional[str] = None
    similarity: Optional[float] = None


class RetrievalResponse(BaseModel):
    chunks: List[ChunkResult]
