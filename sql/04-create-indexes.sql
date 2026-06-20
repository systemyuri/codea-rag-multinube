-- Índice HNSW para búsqueda vectorial rápida (opcional pero recomendado)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

-- Índice para búsquedas por hash (usado en la ingesta)
CREATE INDEX IF NOT EXISTS idx_documentos_hash ON documentos_metadata (file_hash);

-- Índice para búsquedas por nombre
CREATE INDEX IF NOT EXISTS idx_documentos_filename ON documentos_metadata (filename);