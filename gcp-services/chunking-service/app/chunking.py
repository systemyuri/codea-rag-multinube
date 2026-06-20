import re
import uuid
from typing import List, Optional

from .models import DocumentChunk

MAX_CHUNK_SIZE_CHARS = 8000
OVERLAP_CHARS = 200


def split_by_articles(text: str, source: str) -> List[DocumentChunk]:
    """Divide texto por artículos (case-insensitive, acepta 'Artículo' o 'Articulo')"""
    chunks = []
    # Patrón: desde "Artículo X" hasta antes del siguiente "Artículo X" o final
    pattern = re.compile(
        r"(Art[íi]culo\s+\d+.*?)(?=(?:Art[íi]culo\s+\d+)|$)", re.DOTALL | re.IGNORECASE
    )
    matches = pattern.finditer(text)
    for match in matches:
        article_text = match.group(1).strip()
        article_num = extract_article_number(article_text)
        if len(article_text) > MAX_CHUNK_SIZE_CHARS:
            sub_chunks = split_long_article(article_text, article_num, source)
            chunks.extend(sub_chunks)
        else:
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    article=article_num,
                    content=article_text,
                    source=source,
                )
            )
    return chunks


def split_by_paragraphs(text: str, source: str) -> List[DocumentChunk]:
    """Divide texto por párrafos (saltos de línea dobles)"""
    chunks = []
    paragraphs = re.split(r"\n\s*\n", text)
    current_chunk = ""
    para_count = 0
    for para in paragraphs:
        if not para.strip():
            continue
        if len(current_chunk) + len(para) + 1 > MAX_CHUNK_SIZE_CHARS and current_chunk:
            chunks.append(create_generic_chunk(current_chunk, source, para_count))
            # Solapamiento: conservar últimos OVERLAP_CHARS
            overlap = (
                current_chunk[-OVERLAP_CHARS:]
                if len(current_chunk) > OVERLAP_CHARS
                else current_chunk
            )
            current_chunk = overlap
            para_count += 1
        if current_chunk:
            current_chunk += "\n\n"
        current_chunk += para
    if current_chunk:
        chunks.append(create_generic_chunk(current_chunk, source, para_count))
    return chunks


def split_document(
    text: str, source: str, has_articles: Optional[bool] = None
) -> List[DocumentChunk]:
    """Método principal: decide qué estrategia usar"""
    if has_articles is None:
        has_articles = bool(re.search(r"(?i)(art[íi]culo|art\.)", text))
    if has_articles:
        return split_by_articles(text, source)
    else:
        return split_by_paragraphs(text, source)


def extract_article_number(text: str) -> str:
    """Extrae el número del artículo (ej: 'Artículo 42' -> '42')"""
    match = re.search(r"(?i)Art[íi]culo\s+(\d+)", text)
    return match.group(1) if match else "UNKNOWN"


def split_long_article(
    article_text: str, article_num: str, source: str
) -> List[DocumentChunk]:
    """Divide un artículo muy largo en sub-fragmentos por oraciones"""
    sentences = re.split(r"(?<=[.!?])\s+", article_text)
    sub_chunks = []
    buffer = ""
    part_idx = 1
    for sent in sentences:
        if len(buffer) + len(sent) + 1 > MAX_CHUNK_SIZE_CHARS and buffer:
            sub_chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    article=f"{article_num}-{part_idx}",
                    content=buffer.strip(),
                    source=source,
                )
            )
            buffer = ""
            part_idx += 1
        if buffer:
            buffer += " "
        buffer += sent
    if buffer:
        sub_chunks.append(
            DocumentChunk(
                id=str(uuid.uuid4()),
                article=f"{article_num}-{part_idx}",
                content=buffer.strip(),
                source=source,
            )
        )
    return sub_chunks


def create_generic_chunk(content: str, source: str, idx: int) -> DocumentChunk:
    return DocumentChunk(
        id=str(uuid.uuid4()), article=f"SECCION_{idx}", content=content, source=source
    )
