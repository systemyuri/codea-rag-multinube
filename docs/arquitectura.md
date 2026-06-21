# 🏗️ Arquitectura del Sistema – CODEA RAG

**Autor:** David Yurvilca  
**Fecha:** Junio 2026  
**Versión:** 1.0  

---

## 📌 Resumen de la Arquitectura

CODEA RAG es una plataforma **serverless multi‑cloud** diseñada para responder preguntas en lenguaje natural sobre pensión de alimentos en Perú. Su arquitectura distribuye los componentes entre tres proveedores cloud para aprovechar las fortalezas de cada uno:

- **Microsoft Azure:** Frontend, orquestación, LLM y observabilidad.
- **Amazon Web Services (AWS):** Ingesta y almacenamiento de documentos.
- **Google Cloud Platform (GCP):** Procesamiento de texto, búsqueda vectorial y base de datos.

El sistema implementa el patrón de diseño **RAG Básico + Self-Query Retriever**, combinando búsqueda semántica con filtros por metadatos.

---

## 🧩 Componentes por Proveedor

### 1. Microsoft Azure (Capa de Presentación y Orquestación)

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Frontend** | Azure Static Web Apps (React + Vite) | Interfaz de usuario para que los ciudadanos realicen consultas y visualicen respuestas. |
| **Orquestador** | Azure Functions (Python) | Gestiona el flujo RAG: recibe preguntas, invoca embeddings, llama al retrieval service, construye prompts y genera respuestas finales. |
| **LLM** | Azure OpenAI (GPT-4o, text-embedding-3) | Genera embeddings semánticos de las preguntas y produce respuestas en lenguaje natural. |
| **Observabilidad** | Application Insights | Monitorea el rendimiento de las Functions, errores, latencia y dependencias. |

### 2. Amazon Web Services (Capa de Ingesta)

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Almacenamiento** | AWS S3 | Almacena los PDFs de normas legales subidos por el administrador. Actúa como origen de eventos para la ingesta. |
| **Ingesta Automática** | AWS Lambda (Python) | Se activa al subir un nuevo PDF a S3. Valida el hash (evita duplicados), envía el documento al Chunking Service y actualiza el estado en la base de datos. |

### 3. Google Cloud Platform (Capa de Procesamiento y Almacenamiento Vectorial)

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Chunking Service** | Cloud Run (FastAPI, Python) | Recibe un PDF, extrae el texto, lo fragmenta en chunks (con tamaño y solapamiento configurables), genera embeddings (usando Azure OpenAI) y los almacena en AlloyDB. |
| **Retrieval Service** | Cloud Run (FastAPI, Python) | Recibe un vector (embedding de la pregunta) y filtros (norm_code, título). Realiza una búsqueda por similitud coseno en AlloyDB aplicando los filtros, y devuelve los chunks más relevantes. |
| **Base de Datos Vectorial** | GCP AlloyDB + pgvector | Almacena los chunks, sus embeddings (vectores) y los metadatos de los documentos (norm_code, título, nombre de archivo). |

---

## 🔀 Flujos de Datos

### Flujo de Consulta del Usuario (RAG en línea)

1. **Usuario → Frontend:** El usuario escribe una pregunta en lenguaje natural (ej. "¿Qué dice la Ley 27337?").
2. **Frontend → Orquestador:** Se envía un `POST /ask` a la Azure Function.
3. **Orquestador → Self-Query:** La función `extraer_filtros()` aplica expresiones regulares para extraer `norm_code` o `title` de la pregunta.
4. **Orquestador → Embeddings:** Llama a Azure OpenAI para generar un vector (embedding) de la pregunta.
5. **Orquestador → Retrieval Service:** Envía el vector y los filtros al servicio de retrieval en GCP.
6. **Retrieval Service → AlloyDB:** Ejecuta una consulta SQL con `ORDER BY embedding <-> %s::vector` y filtros `WHERE`, devolviendo los *top‑k* chunks.
7. **Retrieval Service → Orquestador:** Devuelve los chunks (texto, artículo, metadatos).
8. **Orquestador → LLM:** Construye un prompt con los chunks y la pregunta original, y lo envía a Azure OpenAI (GPT-4o).
9. **LLM → Orquestador:** Genera la respuesta final con las citas entre corchetes `[Ley 27337, Art. 164]`.
10. **Orquestador → Frontend → Usuario:** La respuesta se muestra en la interfaz.

### Flujo de Ingesta de Documentos (Offline)

1. **Administrador → S3:** Sube un PDF al bucket S3 (con metadatos: `hash`, `title`, `norm_code`).
2. **S3 → Lambda:** El evento de subida activa la función Lambda.
3. **Lambda → Chunking Service:** Valida el hash contra la base de datos para evitar duplicados y envía el PDF al servicio de chunking en GCP.
4. **Chunking Service → Extracción:** Extrae el texto del PDF, lo fragmenta en chunks, genera embeddings (Azure OpenAI) y los almacena en AlloyDB junto con los metadatos.

---

## 🌐 Red y Conectividad Cross‑Cloud

| Origen | Destino | Método | Justificación |
|--------|---------|--------|---------------|
| Azure Function (Azure) | Retrieval Service (GCP) | Llamada HTTPS pública (con timeout controlado) | Simplicidad y baja latencia; GCP Cloud Run está expuesto de forma pública con autenticación opcional. |
| AWS Lambda (AWS) | Chunking Service (GCP) | Llamada HTTPS pública | Similar al caso anterior; los servicios están autenticados mediante variables de entorno. |
| Frontend (Azure) | Azure Function (Azure) | HTTPS (dominio público) | Azure Static Web Apps y Functions están en el mismo tenant de Azure, pero se comunican vía internet pública con autenticación. |
| Cloud Run (GCP) | AlloyDB (GCP) | Conexión interna (VPC) | Cloud Run está conectado a la misma VPC que AlloyDB mediante un VPC Connector, garantizando baja latencia y seguridad. |

---

## 🔐 Seguridad y Autenticación

| Capa | Mecanismo | Descripción |
|------|-----------|-------------|
| **Frontend → Azure Function** | JWT (Bearer Token) | El administrador inicia sesión en `/login` y obtiene un token JWT que se envía en el header `Authorization` para endpoints protegidos (ej. listar documentos). |
| **Azure Function → Azure OpenAI** | API Key | Se utiliza la clave de API de Azure OpenAI (configurada como variable de entorno). |
| **AWS Lambda → GCP** | URLs públicas (sin autenticación adicional) | El chunking service está expuesto, pero solo procesa llamadas que contienen un archivo válido; se asume que la seguridad perimetral de la red es suficiente o se maneja mediante whitelisting de IPs (si se configura). |
| **Cloud Run → AlloyDB** | Credenciales de base de datos (env vars) | Se inyectan `DB_USER`, `DB_PASSWORD`, `DB_HOST` como variables de entorno; la conexión se realiza dentro de la VPC de GCP. |
| **AWS Lambda → S3** | IAM Roles | La Lambda tiene un rol IAM que le permite leer objetos del bucket S3. |

---

## 📊 Observabilidad y Trazabilidad

| Proveedor | Herramienta | Uso |
|-----------|-------------|-----|
| Azure | Application Insights | Monitoreo de Functions (duración, errores, dependencias). |
| AWS | CloudWatch | Logs de Lambda y métricas de invocaciones. |
| GCP | Cloud Logging / Cloud Monitoring | Logs de Cloud Run y métricas de CPU/memoria/latencia. |

**Trazabilidad:** Se utiliza un `correlationId` generado en el frontend y propagado en todas las llamadas, permitiendo seguir una solicitud a través de los tres proveedores.

---

## 🗺️ Diagrama de Arquitectura

El diagrama visual completo está disponible en el archivo [`arquitectura.mermaid`](arquitectura.mermaid). Puedes visualizarlo en GitHub o en el [Mermaid Live Editor](https://mermaid.live/).

---

## 📌 Decisiones Técnicas Relevantes

| Decisión | Justificación |
|----------|---------------|
| **Self-Query Retriever** | Mejora la precisión de la recuperación sin añadir costo (usa regex en lugar de un LLM para extraer filtros). |
| **Azure OpenAI vs. Bedrock** | Se eligió Azure porque el curso y el ecosistema del equipo ya estaban familiarizados con Azure; además, el pricing de GPT-4o es competitivo. |
| **AlloyDB vs. Cloud SQL** | AlloyDB ofrece mejor rendimiento para cargas de trabajo de vectores y está optimizado para PostgreSQL, con pgvector incluido. |
| **Cloud Run vs. Compute Engine** | Cloud Run es serverless, escala a cero y es más rentable para cargas de trabajo con tráfico variable. |
| **S3 + Lambda vs. Azure Blob + Function** | AWS S3 ofrece un almacenamiento de objetos muy robusto con eventos integrados; Lambda es una opción serverless madura y de bajo costo. |

---

## 📚 Documentos Relacionados

- [Diagrama de Arquitectura (Mermaid)](arquitectura.mermaid) – Visualización gráfica.
- [Guía de Administrador](guia-administrador.md) – Detalles de despliegue y configuración.
- [Patrón de Diseño LLM](patron-diseno-llm.md) – Explicación del Self-Query Retriever.
- [README Principal](../README.md) – Visión general del proyecto.

---

**Autor:** David Yurvilca  
**Fecha:** Junio 2026  
**Versión:** 1.0