import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
from .models import ChunkResult

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", "5432"),
        database=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD")
    )

def search_similar_chunks(vector: List[float], limit: int = 5) -> List[ChunkResult]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Convertir la lista de Python a un literal vector para PostgreSQL
    vector_str = "[" + ",".join(str(x) for x in vector) + "]"
    sql = """
        SELECT content, source, article, norm_code
        FROM chunks
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """
    cur.execute(sql, (vector_str, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [ChunkResult(**row) for row in rows]