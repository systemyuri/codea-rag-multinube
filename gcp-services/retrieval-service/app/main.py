import logging
import traceback

from fastapi import FastAPI, HTTPException

from .models import RetrievalRequest, RetrievalResponse
from .retrieval import search_similar_chunks

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Retrieval Service",
    description="Búsqueda de fragmentos vectoriales en AlloyDB con filtros Self-Query",
)


@app.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    try:
        if not request.vector or len(request.vector) != 1536:
            raise HTTPException(
                status_code=400, detail="El vector debe tener 1536 dimensiones"
            )

        logger.info(
            f"📥 Solicitud recibida: limit={request.limit}, filtros={request.filtros}"
        )

        chunks = search_similar_chunks(
            request.vector, limit=request.limit, filtros=request.filtros
        )
        return RetrievalResponse(chunks=chunks)

    except HTTPException:
        raise  # Re-lanzar excepciones HTTP ya manejadas
    except Exception as e:
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"❌ Error en /retrieve: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug/columns")
async def debug_columns():
    """
    Endpoint de depuración: devuelve los nombres de las columnas de las tablas.
    """
    from .retrieval import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documentos_metadata'
            ORDER BY ordinal_position;
        """)
        metadata_cols = cur.fetchall()
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chunks'
            ORDER BY ordinal_position;
        """)
        chunks_cols = cur.fetchall()
        return {"documentos_metadata": metadata_cols, "chunks": chunks_cols}
    finally:
        cur.close()
        conn.close()
