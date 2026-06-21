import datetime
import json
import logging
import os
import random
import re
import time

import azure.functions as func
import boto3
import jwt
import psycopg2
import requests
from psycopg2.extras import RealDictCursor

app = func.FunctionApp()

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
EMBEDDING_DEPLOYMENT = os.environ.get("EMBEDDING_DEPLOYMENT", "embedding3")
CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT", "gpt4o")
RETRIEVAL_URL = os.environ.get("RETRIEVAL_URL")

JWT_SECRET = os.environ.get("JWT_SECRET", "D3M0S14R4G")
TOKEN_EXPIRY = int(os.environ.get("TOKEN_EXPIRY_MINUTES", 60))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "ArquitecturaIA-2026")

# Configuración de AWS
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "codea-docs-ingesta")


# Configuración de AlloyDB
DB_HOST = os.environ.get("DB_HOST")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")


def extraer_filtros(pregunta: str) -> dict:
    filtros = {}
    # Patrón más flexible: captura "Ley", "Decreto", etc., y luego números (con guiones)
    # patron_norma = r"(ley|decreto legislativo|decreto supremo|resolucion administrativa|constitucion politica)\s*([0-9-]+)"
    # match = re.search(patron_norma, pregunta, re.IGNORECASE)
    match = re.search(
        r"(?i)\b(ley|decreto legislativo|decreto supremo|resolucion administrativa|constitucion politica)\s*([0-9-]+)",
        pregunta,
    )
    if match:
        tipo = match.group(1).strip().upper()
        numero = match.group(2).strip()
        # Normalizar el tipo
        if tipo == "LEY":
            filtros["norm_code"] = f"LEY {numero}"
        elif tipo == "DECRETO LEGISLATIVO":
            filtros["norm_code"] = f"DECRETO LEGISLATIVO {numero}"
        elif tipo == "DECRETO SUPREMO":
            filtros["norm_code"] = f"Decreto Supremo {numero}"
        elif "RESOLUCION" in tipo:
            filtros["norm_code"] = f"RESOLUCION ADMINISTRATIVA {numero}"
        elif "CONSTITUCION" in tipo:
            filtros["norm_code"] = "CONSTITUCION POLITICA 1993"
        else:
            filtros["norm_code"] = f"{tipo} {numero}"

    # También buscar títulos entre comillas
    match_titulo = re.search(r'"(.*?)"', pregunta)
    if match_titulo:
        filtros["title_exact"] = match_titulo.group(1).strip()

    return filtros


def get_embedding(text, retries=5):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_DEPLOYMENT}/embeddings?api-version=2024-10-21"
    headers = {"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"}
    payload = {"input": text}
    for attempt in range(retries):
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 429:
            wait = (2**attempt) + random.uniform(0, 1)
            logging.warning(f"Rate limit en embeddings. Esperando {wait:.2f}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    raise Exception("No se pudo obtener embedding después de reintentos")


def retrieve_context(vector, limit=20, filtros=None):
    url = f"{RETRIEVAL_URL}/retrieve"
    payload = {"vector": vector, "limit": limit}
    if filtros:
        payload["filtros"] = filtros
    resp = requests.post(url, json=payload, timeout=30)
    logging.info(f"[DEBUG] Status code: {resp.status_code}")
    logging.info(f"[DEBUG] Respuesta completa: {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()
    chunks = data.get("chunks", [])
    logging.info(f"[DEBUG] Número de chunks obtenidos: {len(chunks)}")
    return chunks


def build_prompt(question, chunks):
    context_parts = []
    for c in chunks:
        article = c.get("article", "Sin artículo")
        content = c.get("content", "")
        context_parts.append(f"[{article}] {content}")
    context = "\n\n".join(context_parts)
    prompt = f"""Eres un asistente legal experto en normas peruanas de alimentos.

**Instrucciones estrictas (sigue estas reglas al pie de la letra):**
1. **Responde ÚNICAMENTE** usando la información de los fragmentos proporcionados.
2. **Para preguntas de listado o enumeración**: devuelve SOLO la lista, sin introducciones ni explicaciones adicionales. Usa el mismo formato y orden que aparece en la ley.
3. **Para preguntas de definición o concepto**: da una respuesta concisa (máximo 2 oraciones), usando exactamente las mismas palabras que aparecen en el fragmento.
4. **Para preguntas de fechas, plazos o números**: escríbelos EXACTAMENTE como aparecen en la ley (ej. "cinco (5) días", "tres (3) cuotas").
5. **No añadas información que no esté en los fragmentos.** Si la respuesta no se encuentra, di: "No se encontró información en los documentos disponibles."
6. **Incluye SIEMPRE la fuente entre corchetes al final de cada respuesta, ej. [Ley 28970, Art. 1]**.

### Fragmentos:
{context}

### Pregunta:
{question}

### Respuesta (sigue las reglas anteriores):"""
    return prompt


def get_chat_completion(prompt, retries=5):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{CHAT_DEPLOYMENT}/chat/completions?api-version=2024-10-21"
    headers = {"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"}
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }
    for attempt in range(retries):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 429:
            wait = (2**attempt) + random.uniform(0, 1)
            logging.warning(f"Rate limit en chat. Esperando {wait:.2f}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    raise Exception("No se pudo obtener respuesta del chat después de reintentos")


@app.route(route="ask", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        question = req_body.get("question")
        if not question:
            return func.HttpResponse("Falta 'question' en el cuerpo", status_code=400)

        logging.info(f"📝 Pregunta recibida: {question}")

        # Paso 1: Extraer filtros
        filtros = extraer_filtros(question)
        logging.info(f"🔍 Filtros extraídos: {filtros}")

        # Paso 2: Generar embedding
        logging.info("🔄 Generando embedding...")
        vector = get_embedding(question)
        logging.info("✅ Embedding generado.")

        # Paso 3: Recuperar chunks
        logging.info("🔎 Recuperando chunks...")
        chunks = retrieve_context(vector, limit=20, filtros=filtros)
        logging.info(f"📦 Número de chunks recuperados: {len(chunks)}")

        # === DEPURACIÓN: Mostrar el primer chunk ===
        if chunks:
            logging.info(
                f"📄 Primer chunk: {json.dumps(chunks[0], ensure_ascii=False)}"
            )
        else:
            logging.warning("⚠️ No se encontraron chunks.")

        # Paso 4: Verificar si hay chunks
        if not chunks:
            return func.HttpResponse(
                json.dumps(
                    {
                        "answer": "No se encontraron fragmentos relevantes.",
                        "debug_retrieval_url": RETRIEVAL_URL,
                        "debug_chunks": chunks,
                    },
                    ensure_ascii=False,
                ),
                mimetype="application/json",
                status_code=200,
            )

        # Paso 5: Construir el prompt
        logging.info("📝 Construyendo prompt...")
        prompt = build_prompt(question, chunks)
        logging.info(f"📄 Prompt (primeros 200 caracteres): {prompt[:200]}...")

        # Paso 6: Obtener respuesta del chat
        logging.info("🤖 Llamando a Azure OpenAI...")
        answer = get_chat_completion(prompt)
        logging.info("✅ Respuesta generada.")

        return func.HttpResponse(
            json.dumps({"answer": answer}, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"❌ Error en ask: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )


@app.route(route="login", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def login(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            # Generar JWT
            token = jwt.encode(
                {
                    "sub": username,
                    "exp": datetime.datetime.utcnow()
                    + datetime.timedelta(minutes=TOKEN_EXPIRY),
                    "iat": datetime.datetime.utcnow(),
                },
                JWT_SECRET,
                algorithm="HS256",
            )
            return func.HttpResponse(
                json.dumps({"token": token, "expires_in": TOKEN_EXPIRY * 60}),
                mimetype="application/json",
                status_code=200,
            )
        else:
            return func.HttpResponse("Credenciales inválidas", status_code=401)
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return func.HttpResponse("Error en el servidor", status_code=500)


def validate_jwt(req):
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise Exception("Token no proporcionado")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expirado")
    except jwt.InvalidTokenError:
        raise Exception("Token inválido")


@app.route(route="documents", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def list_documents(req: func.HttpRequest) -> func.HttpResponse:
    try:
        validate_jwt(req)  # Protegido
        search = req.params.get("search", "")
        limit = int(req.params.get("limit", 20))
        offset = int(req.params.get("offset", 0))

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Consulta con búsqueda
        sql = """
            SELECT id, filename, file_hash, uploaded_at, processed, file_size_bytes
            FROM documentos_metadata
            WHERE filename ILIKE %s
            ORDER BY uploaded_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, (f"%{search}%", limit, offset))
        rows = cur.fetchall()
        cur.execute(
            "SELECT COUNT(*) FROM documentos_metadata WHERE filename ILIKE %s",
            (f"%{search}%",),
        )
        total = cur.fetchone()["count"]
        cur.close()
        conn.close()

        return func.HttpResponse(
            json.dumps({"documents": rows, "total": total}, default=str),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error en list_documents: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e), "documents": [], "total": 0}),
            mimetype="application/json",
            status_code=500,
        )


# Cliente S3
def get_s3_client():
    try:
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )
    except Exception as e:
        logging.error(f"Error creando cliente S3: {str(e)}")
        return None


@app.route(
    route="documents/delete", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS
)
def delete_document(req: func.HttpRequest) -> func.HttpResponse:
    doc_id = req.params.get("id")
    if not doc_id:
        return func.HttpResponse("Falta el parámetro 'id'", status_code=400)
    try:
        validate_jwt(req)
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener el nombre del archivo antes de eliminar (para borrar de S3)
        cur.execute("SELECT filename FROM documentos_metadata WHERE id = %s", (doc_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return func.HttpResponse("Documento no encontrado", status_code=404)
        filename = row[0]
        s3_client = get_s3_client()
        # Eliminar de S3
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=filename)
        except Exception as e:
            logging.error(f"Error al eliminar de S3: {str(e)}")
            # Continuamos para eliminar de la DB

        # Eliminar de la base de datos (ON DELETE CASCADE eliminará chunks si existe FK)
        cur.execute("DELETE FROM documentos_metadata WHERE id = %s", (doc_id,))
        conn.commit()
        cur.close()
        conn.close()

        return func.HttpResponse(
            json.dumps({"message": f"Documento {filename} eliminado correctamente"}),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error eliminando: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(
    route="documents/download", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def download_document(req: func.HttpRequest) -> func.HttpResponse:
    doc_id = req.params.get("id")
    if not doc_id:
        return func.HttpResponse("Falta el parámetro 'id'", status_code=400)
    try:
        validate_jwt(req)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM documentos_metadata WHERE id = %s", (doc_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return func.HttpResponse("Documento no encontrado", status_code=404)
        filename = row[0]
        s3_client = get_s3_client()
        # Generar URL prefirmada (válida por 60 segundos)
        presigned_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": filename}, ExpiresIn=60
        )
        return func.HttpResponse(
            json.dumps({"download_url": presigned_url}),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error generando URL: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )


@app.route(route="upload", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def upload(req: func.HttpRequest) -> func.HttpResponse:
    try:
        validate_jwt(req)
        file = req.files.get("file")
        if not file:
            return func.HttpResponse(
                json.dumps({"error": "Falta el archivo"}),
                status_code=400,
                mimetype="application/json",
            )

        filename = file.filename
        if not filename or not filename.lower().endswith(".pdf"):
            return func.HttpResponse(
                json.dumps({"error": "Solo se permiten archivos PDF"}),
                status_code=400,
                mimetype="application/json",
            )

        file_hash = req.form.get("hash")
        if not file_hash:
            return func.HttpResponse(
                json.dumps({"error": "Falta el hash"}),
                status_code=400,
                mimetype="application/json",
            )

        # === Recibir título y código ===
        title = req.form.get("title", "")
        norm_code = req.form.get("normCode", "")

        file_content = file.read()
        file_size = len(file_content)

        # Subir a S3 con metadatos
        s3_client = get_s3_client()
        if s3_client is None:
            return func.HttpResponse(
                json.dumps({"error": "Error de configuración S3"}),
                status_code=500,
                mimetype="application/json",
            )

        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=filename,
                Body=file_content,
                ContentType="application/pdf",
                Metadata={"hash": file_hash, "title": title, "norm_code": norm_code},
            )
        except Exception as e:
            logging.error(f"Error subiendo a S3: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": "Error al subir a S3"}),
                status_code=500,
                mimetype="application/json",
            )

        # Guardar en documentos_metadata con título y código
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO documentos_metadata (filename, file_hash, file_size_bytes, title, norm_code, processed)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """,
            (filename, file_hash, file_size, title, norm_code),
        )
        conn.commit()
        cur.close()
        conn.close()

        return func.HttpResponse(
            json.dumps(
                {
                    "message": f"Archivo {filename} subido correctamente",
                    "hash": file_hash,
                    "title": title,
                    "norm_code": norm_code,
                }
            ),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error en upload: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json"
        )
