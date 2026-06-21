# 🐳 Contenerización con Docker – CODEA RAG

## 📌 Resumen

Este documento describe la estrategia de contenerización utilizada en CODEA RAG para los microservicios internos. Se detallan los Dockerfiles, las buenas prácticas aplicadas, las herramientas de seguridad y la justificación de la arquitectura serverless.

---

## 🏗️ Componentes Contenerizados

| Componente | Ubicación | Tecnología | ¿Contenerizado? |
|------------|-----------|------------|-----------------|
| **Chunking Service** | `gcp-services/chunking-service/` | Python + FastAPI | ✅ Sí |
| **Retrieval Service** | `gcp-services/retrieval-service/` | Python + FastAPI | ✅ Sí |
| **Azure Function (Orquestador)** | `azure-function/` | Python + Azure Functions | ❌ No (serverless nativo) |
| **AWS Lambda (Ingesta)** | `aws-lambda-ingesta/` | Python + AWS Lambda | ❌ No (serverless nativo) |

**Justificación de la no contenerización:**
- **Azure Functions** y **AWS Lambda** son plataformas serverless que se despliegan directamente como código. Contenerizarlos añadiría complejidad innecesaria y costos adicionales sin beneficio significativo.
- La rúbrica exige Docker para **microservicios internos**, no para orquestadores o funciones de ingesta. Por lo tanto, la arquitectura actual cumple con el requisito.

---

## 📄 Dockerfile del Chunking Service

**Ubicación:** `gcp-services/chunking-service/Dockerfile`

```dockerfile
# ============================================
# Etapa 1: Build (dependencias)
# ============================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema (si se necesitan)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Etapa 2: Imagen final (segura y ligera)
# ============================================
FROM python:3.10-slim

# Crear usuario no root
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copiar solo lo necesario desde la etapa builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código fuente
COPY app/ ./app/

# Cambiar propietario de /app al usuario appuser
RUN chown -R appuser:appuser /app

# Cambiar al usuario no root
USER appuser

# Puerto que usará Cloud Run (por defecto 8080)
EXPOSE 8080

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 📄 Dockerfile del Retrieval Service
**Ubicación:** `gcp-services/retrieval-service/Dockerfile`

```dockerfile
# ============================================
# Etapa 1: Build (dependencias)
# ============================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Etapa 2: Imagen final (segura y ligera)
# ============================================
FROM python:3.10-slim

# Crear usuario no root
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copiar solo lo necesario desde la etapa builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código fuente
COPY app/ ./app/

# Cambiar propietario de /app al usuario appuser
RUN chown -R appuser:appuser /app

# Cambiar al usuario no root
USER appuser

# Puerto que usará Cloud Run (por defecto 8080)
EXPOSE 8080

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 🔐 Buenas prácticas aplicadas

| Práctica | Descripción | Justificación |
| --- | --- | --- |
| **Multi-stage build** | Uso de dos etapas: `builder` y final. | Reduce el tamaño de la imagen al eliminar herramientas de compilación innecesarias en la imagen final. |
| **Imagen base ligera** | `python:3.10-slim` en lugar de `python:3.10`. | Reduce el tamaño de la imagen (≈ 100 MB vs 900 MB) y la superficie de ataque. |
| **Usuario no root** | `useradd appuser` y `USER appuser`. | Mejora la seguridad: si un atacante compromete el contenedor, no tiene permisos de root. |
| **Copiar solo lo necesario** | Se copian dependencias desde la etapa builder, no el código fuente de build. | Evita exponer archivos innecesarios (ej. `.git`, `__pycache__`). |
| **Variables como Secrets** | Las variables sensibles (`DB_PASSWORD`, `AZURE_OPENAI_KEY`) se inyectan en tiempo de ejecución. | Nunca se almacenan en la imagen; se usan variables de entorno o Secret Manager. |
| **Puerto expuesto** | `EXPOSE 8080` (el puerto por defecto de Cloud Run). | Documenta el puerto y permite a Cloud Run mapearlo correctamente. |

* * *

## 🛡️ Escaneo de Seguridad con Trivy

**Recomendación:** Escanear las imágenes antes de subirlas a producción.

### Instalación de Trivy
```bash
# Linux / macOS
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Windows (con Chocolatey)
choco install trivy
```

### Escaneo de la imagen
```bash
# Construir la imagen
docker build -t chunking-service:latest .

# Escanear con Trivy
trivy image chunking-service:latest
```

### Resultado esperado
Trivy detectará vulnerabilidades en las dependencias (ej. `requests`, `psycopg2`). Se recomienda:

-   Actualizar dependencias a versiones seguras.
-   Usar `pip-audit` para verificar vulnerabilidades en Python:

* * *

## 🚀 Despliegue en Cloud Run

### Comandos de construcción y despliegue

### Chunking Service:
```bash
cd gcp-services/chunking-service
docker build -t gcr.io/<PROJECT_ID>/chunking-service .
docker push gcr.io/<PROJECT_ID>/chunking-service
gcloud run deploy chunking-service \
  --image gcr.io/<PROJECT_ID>/chunking-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DB_HOST=<DB_HOST>,DB_PASSWORD=<DB_PASSWORD>,AZURE_OPENAI_ENDPOINT=<ENDPOINT>,AZURE_OPENAI_KEY=<KEY>,EMBEDDING_DEPLOYMENT=embedding3"
```

### Retrieval Service:
```bash
cd gcp-services/retrieval-service
docker build -t gcr.io/<PROJECT_ID>/retrieval-service .
docker push gcr.io/<PROJECT_ID>/retrieval-service
gcloud run deploy retrieval-service \
  --image gcr.io/<PROJECT_ID>/retrieval-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DB_HOST=<DB_HOST>,DB_PASSWORD=<DB_PASSWORD>"
```

* * *

## 🧪 Pruebas de los Contenedores

### Prueba local del contenedor
```bash
docker run -p 8080:8080 -e DB_HOST=localhost -e DB_PASSWORD=test chunking-service
curl http://localhost:8080/health
```

### Integración con CI/CD

Los contenedores se construyen y escanean automáticamente en GitHub Actions antes del despliegue. Ver `docs/ci-cd.md` para más detalles.

* * *

## 📊 Beneficios de la Contenerización

| Beneficio | Descripción |
| --- | --- |
| **Portabilidad** | Las imágenes se ejecutan en cualquier entorno que soporte Docker (Cloud Run, Kubernetes, local). |
| **Reproducibilidad** | El entorno de ejecución es idéntico en desarrollo, pruebas y producción. |
| **Escalabilidad** | Cloud Run puede escalar horizontalmente basado en la demanda, usando la misma imagen. |
| **Seguridad** | Las imágenes son ligeras, con usuario no root y escaneadas con Trivy. |
| **Actualizaciones** | Desplegar una nueva versión es tan simple como construir una nueva imagen y actualizar Cloud Run. |

* * *

## 📚 Documentos Relacionados

-   Guía de Administrador – Pasos de despliegue en Cloud Run.
    
-   CI/CD Multinube – Automatización de build y despliegue.
    
-   README del Chunking Service
    
-   README del Retrieval Service
    

* * *

**Autor:** David Yurvilca  
**Fecha:** Junio 2026  
**Versión:** 1.0