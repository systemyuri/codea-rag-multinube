# chunking-service

## 📌 Finalidad

Este microservicio, desplegado en **Cloud Run (GCP)**, se encarga de dividir el texto extraído de documentos PDF en fragmentos semánticos (chunks) adecuados para la generación de embeddings y su posterior almacenamiento en la base de datos vectorial.

**Flujo de trabajo**:
1. Recibe una petición POST con el texto completo de un documento (extraído previamente por la Lambda de AWS).
2. Detecta automáticamente si el texto tiene estructura de artículos (por la presencia de palabras como "Artículo").
3. Si tiene artículos:
   - Divide el texto por cada artículo (respetando el número y contenido).
   - Si un artículo es demasiado largo, lo subdivide en fragmentos más pequeños (respetando oraciones).
4. Si no tiene artículos:
   - Divide el texto por párrafos (saltos de línea dobles).
   - Agrupa párrafos hasta alcanzar un tamaño máximo (configurable).
5. Devuelve una lista de fragmentos en formato JSON, cada uno con:
   - `id`: UUID único.
   - `article`: número de artículo (o `SECCION_X` si no hay artículos).
   - `content`: texto del fragmento.
   - `source`: nombre del documento original (se pasa en la petición).

---

## 📁 Estructura del directorio


```bash
gcp-services/chunking-service/
├── app/
│ ├── init.py
│ ├── main.py # Punto de entrada FastAPI
│ ├── chunking.py # Lógica de fragmentación (artículos, párrafos)
│ └── models.py # Modelos Pydantic para la API
├── Dockerfile # Configuración para construir la imagen
├── requirements.txt # Dependencias Python
└── deploy-chunking-service.sh # Script de despliegue automatizado
```

### Descripción de archivos

| Archivo | Propósito |
|---------|-----------|
| `app/main.py` | Define los endpoints de la API (`/chunk`, `/health`) y configura Swagger UI (`/docs`). |
| `app/chunking.py` | Contiene la lógica de fragmentación: `split_by_articles`, `split_by_paragraphs`, `split_long_article`, etc. |
| `app/models.py` | Define los modelos de solicitud (`ChunkRequest`) y respuesta (`ChunkResponse`, `DocumentChunk`). |
| `Dockerfile` | Construye la imagen usando Python 3.11-slim y ejecuta `uvicorn`. |
| `requirements.txt` | Dependencias: `fastapi`, `uvicorn`, `python-multipart`, `pydantic`. |
| `deploy-chunking-service.sh` | Automatiza la construcción de la imagen, subida a Google Container Registry (GCR) y despliegue en Cloud Run. |

---

## ✅ Requisitos previos

### Cuentas y permisos
- **GCP**: Proyecto con facturación habilitada, APIs de Cloud Run y Cloud Build activadas.
- **IAM**: La cuenta de servicio que ejecuta el despliegue debe tener roles:
  - `roles/cloudbuild.builds.editor`
  - `roles/run.admin`
  - `roles/iam.serviceAccountUser`

### Herramientas instaladas
- **Google Cloud SDK (`gcloud`)** – configurado con el proyecto activo.
- **Docker** (opcional, si se construye localmente).
- **Git Bash** (Windows) o **Bash** (Linux/Mac) para ejecutar el script.

---

## 🚀 Despliegue

### Automático (recomendado)

El script `deploy-chunking-service.sh` realiza todo el proceso en un solo paso:

```bash
cd gcp-services/chunking-service
chmod +x deploy-chunking-service.sh
./deploy-chunking-service.sh
```

### Qué hace el script:

1.  Verifica que `gcloud` esté instalado.
    
2.  Configura el proyecto activo.
    
3.  Habilita las APIs necesarias (`cloudbuild.googleapis.com`, `run.googleapis.com`).
    
4.  Construye la imagen usando Cloud Build (sube el código a GCP y construye la imagen remotamente).
    
5.  Despliega la imagen en Cloud Run con:
    
    -   Región: `us-central1` (configurable).
        
    -   Permitir invocaciones no autenticadas (`--allow-unauthenticated`).
        
    -   Tiempo de espera: 3600 segundos.
        
    -   Memoria: 512 MiB.
        
6.  Muestra la URL pública del servicio.

## 🧪 Uso de la API

### Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/chunk` | Fragmenta el texto recibido y devuelve los chunks. |
| `GET` | `/health` | Verifica el estado del servicio. |
| `GET` | `/docs` | Interfaz Swagger UI para probar la API. |
| `GET` | `/redoc` | Documentación ReDoc alternativa. |

### Solicitud (`POST /chunk`)

```json
{
  "text": "Texto completo del documento",
  "source": "nombre_del_archivo.pdf",
  "has_articles": null  // opcional: true/false/null (null = detección automática)
}
```

Ejemplo con `curl`:

```bash
curl -X POST https://chunking-service-...run.app/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artículo 1. Este es el primer artículo. Artículo 2. Este es el segundo.",
    "source": "prueba.pdf"
  }'
```
Respuesta:

```json

{
  "chunks": [
    {
      "id": "aafb47f1-785b-4227-b0bb-2573c8924cc4",
      "article": "1",
      "content": "Artículo 1. Este es el primer artículo.",
      "source": "prueba.pdf"
    },
    {
      "id": "0e5012fb-3cf1-4eb4-aec4-ba6fac908508",
      "article": "2",
      "content": "Artículo 2. Este es el segundo.",
      "source": "prueba.pdf"
    }
  ]
}
```
* * *

## 🔧 Configuración y personalización

### Parámetros en `chunking.py`

| Constante | Valor | Descripción |
| --- | --- | --- |
| `MAX_CHUNK_SIZE_CHARS` | `8000` | Tamaño máximo en caracteres de un fragmento (aproximadamente 2000 tokens). |
| `OVERLAP_CHARS` | `200` | Número de caracteres de solapamiento entre fragmentos largos. |

Estos valores se pueden ajustar según las necesidades del modelo de embeddings (Azure OpenAI soporta hasta 8192 tokens).

### Cambiar región o parámetros de Cloud Run

Modifica el script `deploy-chunking-service.sh` o edita el comando `gcloud run deploy`:

```bash
gcloud run deploy chunking-service \
    --image gcr.io/<PROJECT\_ID\>/chunking-service \
    --platform managed \
    --region us-east1 \        # Cambiar región
    --memory 1Gi \             # Aumentar memoria
    --concurrency 100 \        # Número de peticiones concurrentes
    --min-instances 1          # Mantener una instancia activa (evita cold start)
```


## 🔍 Solución de problemas

### 1\. Error `Connection timed out` al llamar al servicio

Causa: Cloud Run puede tardar en escalar (cold start).  
Solución: Aumenta el tiempo de espera en el cliente (por ejemplo, en la Lambda de AWS, aumenta `timeout` de la petición). También puedes configurar `--min-instances=1` para mantener una instancia activa.

### 2\. Error `429 Too Many Requests` en Azure OpenAI (si se usa para embeddings, aunque este servicio no los genera)

Este servicio no llama directamente a Azure OpenAI, solo fragmenta texto. El problema de rate limit ocurre en otros componentes (Lambda, Function App). Asegúrate de que el chunking no está sobrecargando el sistema; el tiempo de respuesta es generalmente rápido.

### 3\. El texto no se fragmenta correctamente

Causa: El formato del texto puede ser inusual (caracteres especiales, saltos de línea extraños).  
Solución:

-   Verifica que el texto extraído del PDF sea legible.
    
-   Ajusta las expresiones regulares en `chunking.py` si es necesario.
    
-   Prueba con un texto de ejemplo para verificar el comportamiento.
    

### 4\. Error de construcción de la imagen

Causa: El Dockerfile o las dependencias pueden tener problemas.  
Solución:

-   Revisa el `Dockerfile` para verificar la sintaxis.
    
-   Asegúrate de que `requirements.txt` contiene todas las dependencias.
    
-   Si usas Cloud Build, revisa los logs en la consola de GCP.
    

* * *

## 📌 Notas adicionales

-   **Swagger UI**: La documentación interactiva está disponible en `/docs` para probar el endpoint fácilmente.
    
-   **Escalado**: Cloud Run escala automáticamente según la demanda. El tiempo de inicio de una nueva instancia puede tomar unos segundos (cold start).
    
-   **Costos**: Cloud Run tiene un nivel gratuito que incluye 2 millones de solicitudes al mes. El costo adicional es mínimo para un uso moderado.
    
-   **Seguridad**: El servicio está configurado con `--allow-unauthenticated` para que pueda ser invocado por la Lambda de AWS sin autenticación adicional. Si se requiere mayor seguridad, se puede habilitar la autenticación IAM y configurar la Lambda para que use credenciales de GCP.
    

* * *

## 🤝 Contribuciones

Si encuentras un problema o deseas mejorar el servicio, abre un pull request o un issue en el repositorio principal.

* * *

Desarrollado por [David Yurivilca](https://github.com/systemyuri) – Proyecto CODEA RAG.


---

## ✅ ¿Qué cubre este README?

| Sección | Contenido |
|---------|-----------|
| **Finalidad** | Explica el propósito del servicio y su flujo de trabajo. |
| **Estructura** | Lista y describe los archivos en la carpeta. |
| **Requisitos** | Cuentas, herramientas y permisos necesarios. |
| **Despliegue** | Instrucciones automáticas y manuales para Cloud Run. |
| **Uso de la API** | Endpoints, ejemplos de solicitud y respuesta. |
| **Configuración** | Parámetros ajustables en el código. |
| **Solución de problemas** | Problemas comunes y soluciones. |

---
