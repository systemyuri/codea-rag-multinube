import io
import json
import os
import random
import time
import urllib
import uuid

import boto3
import psycopg2
import pypdf
import requests

# Configuración desde variables de entorno
CHUNKING_URL = os.environ["CHUNKING_URL"]
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"]
EMBEDDING_DEPLOYMENT = os.environ["EMBEDDING_DEPLOYMENT"]
DB_HOST = os.environ["DB_HOST"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_USER = os.environ.get("DB_USER", "postgres")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")

s3 = boto3.client("s3")


def get_document_id_by_hash(file_hash):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )
    cur = conn.cursor()
    cur.execute("SELECT id FROM documentos_metadata WHERE file_hash = %s", (file_hash,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None


def extract_text_from_pdf(pdf_bytes):
    """Extrae texto de un PDF usando pypdf"""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def get_embedding(text, retries=5):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_DEPLOYMENT}/embeddings?api-version=2024-10-21"
    headers = {"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"}
    payload = {"input": text}

    for attempt in range(retries):
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 429:
            wait = (2**attempt) + random.uniform(
                0, 1
            )  # 1, 2, 4, 8, 16 segundos + jitter
            print(f"Rate limit alcanzado. Esperando {wait:.2f} segundos...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    raise Exception("Demasiados reintentos por rate limit")


def save_chunk_to_alloydb(chunk, embedding, document_id=None, norm_code="", title=""):
    """Inserta un chunk y su vector en AlloyDB (tabla chunks)"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )
    cur = conn.cursor()
    sql = """
        INSERT INTO chunks (id, content, source, article, norm_code, title, document_id, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
    """
    cur.execute(
        sql,
        (
            str(uuid.uuid4()),
            chunk["content"],
            chunk["source"],
            chunk["article"],
            norm_code,
            title,
            document_id,  # <-- aquí
            embedding,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        print(f"Procesando {key} desde {bucket}")

        head = s3.head_object(Bucket=bucket, Key=key)
        metadata = head.get("Metadata", {})
        file_hash = metadata.get("hash")
        document_id = get_document_id_by_hash(file_hash) if file_hash else None
        norm_code = metadata.get("norm_code", "")
        title = metadata.get("title", "")

        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_bytes = response["Body"].read()
        text = extract_text_from_pdf(pdf_bytes)
        if not text.strip():
            print(f"El PDF {key} no contiene texto extraíble")
            # También marcar como procesado aunque no tenga texto
            mark_as_processed(file_hash)
            return {"statusCode": 200, "body": "No text extracted"}

        chunking_payload = {"text": text, "source": key, "has_articles": None}
        chunk_resp = requests.post(
            f"{CHUNKING_URL}/chunk", json=chunking_payload, timeout=120
        )
        chunk_resp.raise_for_status()
        chunks = chunk_resp.json()["chunks"]
        print(f"Obtenidos {len(chunks)} chunks")

        for idx, chunk in enumerate(chunks):
            print(f"Procesando chunk {idx + 1}/{len(chunks)}: {chunk['article']}")
            embedding = get_embedding(chunk["content"])
            save_chunk_to_alloydb(
                chunk,
                embedding,
                document_id=document_id,
                norm_code=norm_code,
                title=title,
            )

        # Marcar el documento como procesado
        mark_as_processed(file_hash)

        return {
            "statusCode": 200,
            "body": json.dumps(f"Procesado {len(chunks)} chunks de {key}"),
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e


def mark_as_processed(file_hash):
    if not file_hash:
        return
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )
    cur = conn.cursor()
    cur.execute(
        "UPDATE documentos_metadata SET processed = TRUE, processed_at = NOW() WHERE file_hash = %s",
        (file_hash,),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Documento con hash {file_hash} marcado como procesado")
