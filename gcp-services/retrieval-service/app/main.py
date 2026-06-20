from fastapi import FastAPI, HTTPException
from .models import RetrievalRequest, RetrievalResponse
from .retrieval import search_similar_chunks

app = FastAPI(title="Retrieval Service", description="Búsqueda de fragmentos vectoriales en AlloyDB")

@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    if not request.vector or len(request.vector) != 1536:
        raise HTTPException(status_code=400, detail="El vector debe tener 1536 dimensiones")
    chunks = search_similar_chunks(request.vector, request.limit)
    return RetrievalResponse(chunks=chunks)

@app.get("/health")
async def health():
    return {"status": "ok"}