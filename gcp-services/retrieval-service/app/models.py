from pydantic import BaseModel
from typing import List, Optional

class RetrievalRequest(BaseModel):
    vector: List[float]  # lista de 1536 floats
    limit: Optional[int] = 5

class ChunkResult(BaseModel):
    content: str
    source: str
    article: str
    norm_code: Optional[str] = None

class RetrievalResponse(BaseModel):
    chunks: List[ChunkResult]