-- Tabla de metadatos de documentos
CREATE TABLE IF NOT EXISTS documentos_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    file_size_bytes BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    norm_code TEXT,
    title TEXT
);

COMMENT ON TABLE documentos_metadata IS 'Metadatos de los documentos subidos al sistema';