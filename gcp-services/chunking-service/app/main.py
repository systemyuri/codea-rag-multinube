from fastapi import FastAPI, HTTPException

from .chunking import split_document
from .models import ChunkRequest, ChunkResponse

app = FastAPI(
    title="Chunking Service",
    description="Divide textos en fragmentos (chunks) para RAG",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternativo
)


@app.post("/chunk", response_model=ChunkResponse, summary="Fragmentar texto")
async def chunk_text(request: ChunkRequest):
    """
    Recibe un texto y devuelve una lista de fragmentos (chunks).
    - Si `has_articles` es True, fuerza división por artículos.
    - Si es False, divide por párrafos.
    - Si es None, detecta automáticamente.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío")
    chunks = split_document(
        text=request.text, source=request.source, has_articles=request.has_articles
    )
    return ChunkResponse(chunks=chunks)


@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok"}
