-- Tabla principal de chunks (fragmentos vectorizados)
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY,
    content TEXT,
    source TEXT,
    article TEXT,
    norm_code TEXT,
    title TEXT,
    document_id UUID,
    embedding vector(1536)
);

-- (Opcional) Comentarios para documentación
COMMENT ON TABLE chunks IS 'Almacena fragmentos de texto y sus embeddings vectoriales';
COMMENT ON COLUMN chunks.embedding IS 'Vector de 1536 dimensiones (text-embedding-3-small)';