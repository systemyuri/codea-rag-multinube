import logging
import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2 import OperationalError, ProgrammingError
from psycopg2.extras import RealDictCursor

from .models import ChunkResult

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_db_connection():
    """
    Obtiene una conexión a la base de datos con timeout de conexión corto.
    """
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", "5432"),
            database=os.environ.get("DB_NAME", "postgres"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD"),
            connect_timeout=5,  # ← NUEVO: falla rápido si no hay conexión
        )
        logger.info("✅ Conexión a la base de datos establecida.")
        return conn
    except OperationalError as e:
        logger.error(f"❌ Error de conexión a la base de datos: {e}")
        raise  # Relanzamos para que el llamador lo maneje


def build_filter_conditions(filtros: Optional[Dict[str, Any]]) -> tuple:
    """Construye la cláusula WHERE y los parámetros a partir de los filtros."""
    if not filtros:
        return "", []

    conditions = []
    params = []

    if "norm_code" in filtros and filtros["norm_code"]:
        conditions.append("dm.norm_code ILIKE %s")
        params.append(f"%{filtros['norm_code'].strip()}%")

    if "title_exact" in filtros and filtros["title_exact"]:
        conditions.append("dm.title ILIKE %s")
        params.append(f"%{filtros['title_exact']}%")

    if "title" in filtros and filtros["title"]:
        conditions.append("dm.title ILIKE %s")
        params.append(f"%{filtros['title']}%")

    if "filename" in filtros and filtros["filename"]:
        conditions.append("dm.filename ILIKE %s")
        params.append(f"%{filtros['filename']}%")

    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    return where_clause, params


def search_similar_chunks(
    vector: List[float], limit: int = 5, filtros: Optional[Dict[str, Any]] = None
) -> List[ChunkResult]:
    conn = None
    cur = None
    try:
        logger.info("🔍 Conectando a la base de datos...")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Obtener filtros
        where_clause, filter_params = build_filter_conditions(filtros)
        logger.info(f"📋 Where clause: {where_clause}")
        logger.info(f"📦 Parámetros de filtro: {filter_params}")

        # Convertir vector a string para PostgreSQL
        vector_str = "[" + ",".join(str(x) for x in vector) + "]"

        # ========== CORRECCIÓN: Orden correcto de parámetros ==========
        # Los placeholders en la consulta aparecen en este orden:
        # 1. Filtros (WHERE)
        # 2. Vector (proyección)
        # 3. Vector (ORDER BY)
        # 4. Limit
        # Por lo tanto, la lista de parámetros debe ser:
        # filter_params + [vector_str, vector_str, limit]
        # ===============================================================

        sql = f"""
            SELECT 
                c.content,
                c.source,
                c.article,
                c.norm_code,
                dm.title AS document_title,
                dm.filename,
                1 - (c.embedding <=> %s::vector) AS similarity
            FROM chunks c
            INNER JOIN documentos_metadata dm ON c.document_id = dm.id
            WHERE 1=1 {where_clause}
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """

        params = [vector_str] + filter_params + [vector_str, limit]
        logger.info(f"📝 SQL: {sql}")
        logger.info(f"📦 Parámetros completos: {params}")

        cur.execute(sql, params)
        rows = cur.fetchall()
        logger.info(f"✅ Consulta ejecutada. {len(rows)} filas obtenidas.")

        # Convertir a ChunkResult
        results = []
        for row in rows:
            results.append(
                ChunkResult(
                    content=row["content"],
                    source=row["source"],
                    article=row["article"],
                    norm_code=row.get("norm_code"),
                    document_title=row.get("document_title"),
                    filename=row.get("filename"),
                    similarity=float(row["similarity"])
                    if row.get("similarity")
                    else None,
                )
            )
        return results

    except ProgrammingError as e:
        logger.error(f"❌ Error de sintaxis SQL: {e}")
        raise RuntimeError(f"Error en consulta SQL: {e}")
    except OperationalError as e:
        logger.error(f"❌ Error operacional de base de datos: {e}")
        raise RuntimeError(f"Error de base de datos: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
