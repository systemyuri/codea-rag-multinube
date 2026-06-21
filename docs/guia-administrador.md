# 🛠️ Guía de Administrador – CODEA RAG

Esta guía está dirigida al equipo técnico responsable del despliegue, configuración y mantenimiento de la plataforma CODEA RAG.

---

## 🏗️ Arquitectura del Sistema

CODEA RAG es una plataforma serverless multi‑cloud compuesta por:

| Componente | Proveedor | Tecnología |
|------------|-----------|------------|
| **Frontend** | Azure | React + Vite + Tailwind CSS (Azure Static Web Apps) |
| **Orquestador** | Azure | Azure Functions (Python) |
| **LLM y Embeddings** | Azure | Azure OpenAI (GPT-4o, text-embedding-3) |
| **Base de Datos Vectorial** | GCP | AlloyDB + pgvector |
| **Chunking y Retrieval** | GCP | Cloud Run (Python/FastAPI) |
| **Ingesta de Documentos** | AWS | S3 + Lambda (Python) |
| **Evaluación** | Local | RAGAS Framework |
| **Despliegue** | Multi-cloud | GitHub Actions + Terraform (opcional) |

### Diagrama de Arquitectura

El diagrama completo está disponible en [`docs/arquitectura.mermaid`](arquitectura.mermaid).

---

## 🔧 Configuración de Variables de Entorno

Todas las variables de entorno necesarias están documentadas en el README principal y en los READMEs de cada componente. Asegúrate de configurarlas correctamente en cada servicio.

### Variables críticas

| Variable | Servicio | Descripción |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure Functions | Endpoint de Azure OpenAI |
| `AZURE_OPENAI_KEY` | Azure Functions | Clave de API de Azure OpenAI |
| `EMBEDDING_DEPLOYMENT` | Azure Functions | Nombre del deployment de embeddings |
| `CHAT_DEPLOYMENT` | Azure Functions | Nombre del deployment de chat (GPT-4o) |
| `RETRIEVAL_URL` | Azure Functions | URL del retrieval service en Cloud Run |
| `DB_HOST` | Cloud Run / Azure | IP de AlloyDB |
| `DB_PASSWORD` | Cloud Run / Azure | Contraseña de AlloyDB |
| `S3_BUCKET` | AWS Lambda | Nombre del bucket S3 para ingesta |
| `AWS_ACCESS_KEY` / `AWS_SECRET_KEY` | AWS Lambda | Credenciales de AWS |

---

## 🚀 Despliegue de Componentes

### 1. Base de Datos (AlloyDB)

1. Crea una instancia de AlloyDB en GCP.
2. Habilita la extensión `pgvector`:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
3. Ejecuta los scripts SQL en sql/ para crear las tablas e índices.

4. Configura el firewall para permitir conexiones desde Cloud Run y Azure.

### 2. Chunking Service (GCP Cloud Run)
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

### 3. Retrieval Service (GCP Cloud Run)
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

### 4. AWS Lambda (Ingesta)
```bash
cd aws-lambda-ingesta
./deploy-aws-ingesta.sh
```
El script configura:

-   El bucket S3 con trigger de eventos.    
-   La función Lambda con las variables de entorno necesarias.    
-   Los permisos IAM para acceder a S3 y llamar al chunking service.

### 5. Azure Function (Orquestador)
```bash
cd azure-function
func azure functionapp publish codea-orchestrator
```
Asegúrate de configurar las variables de entorno en Azure Portal antes del despliegue.

### 6. Frontend (Azure Static Web Apps)
```bash
cd frontend
npm install
npm run build
# Desplegar usando Azure CLI o GitHub Actions
```

## 🔍 Monitoreo y Observabilidad

### Azure (Function App)

-   **Application Insights:** Ver métricas de rendimiento, errores y logs.
-   **Log Streaming:** En tiempo real desde Azure Portal.
-   **Comando CLI:**

```bash
az webapp log tail --name codea-orchestrator --resource-group codea-rg
```

### AWS (Lambda)

-   **CloudWatch:** Métricas de invocaciones, errores y duración.  
-   **CloudTrail:** Auditoría de acciones.    
-   **Logs:** En CloudWatch Logs.
    

### GCP (Cloud Run)

-   **Cloud Logging:** Logs de cada contenedor.    
-   **Cloud Monitoring:** Métricas de CPU, memoria, latencia y errores.    
-   **Comando CLI:**

```bash
gcloud run services logs tail retrieval-service
```

## 🧪 Evaluación del Sistema (RAGAS)

Para evaluar la calidad del sistema RAG, ejecuta las pruebas en `tests/ragas/`:
```bash
cd tests/ragas
python evaluate_ragas.py
```

**Resultado actual**: Precisión del **77%** (supera el umbral mínimo de 0.7 exigido).

## 🐛 Solución de problemas comunes

### Error: Timeout al llamar al retrieval service

-   **Causa:** La consulta a AlloyDB tarda más de 30 segundos.
    
-   **Solución:** Aumenta el timeout en `retrieve_context` (Azure Function) y en Cloud Run. Crea índices vectoriales en AlloyDB.
    

### Error: "No se encontraron fragmentos relevantes"

-   **Causa:** El filtro no coincide con los metadatos de los documentos.
    
-   **Solución:** Revisa que `norm_code` y `title` en `documentos_metadata` coincidan con los valores extraídos por `extraer_filtros`. Usa `ILIKE` para búsquedas insensibles a mayúsculas.
    

### Error: Columna "documento\_id" no existe

-   **Causa:** En la tabla `chunks`, la columna de clave foránea es `document_id`.
    
-   **Solución:** Actualiza la consulta SQL en `retrieval.py` para usar `c.document_id`.
    

### Error: Conexión rechazada a AlloyDB

-   **Causa:** Cloud Run no tiene acceso a la VPC de AlloyDB.
    
-   **Solución:** Configura un VPC Connector en Cloud Run y asegura que AlloyDB tenga reglas de firewall que permitan el tráfico.
    

* * *

## 🔐 Seguridad

-   **Autenticación:** JWT para el panel de administración (`login`).
    
-   **CORS:** Configurado en Azure Static Web Apps para permitir solo orígenes confiables.
    
-   **Variables sensibles:** Almacenadas como secrets en cada proveedor (Azure Key Vault, AWS Secrets Manager, GCP Secret Manager).
    
-   **Contenedores:** Las imágenes Docker son multi-stage, sin usuario root, y escaneadas con Trivy.
    

* * *

## 💰 Optimización de Costos (FinOps)

Estrategias implementadas:

-   **Caching:** Los chunks recuperados se almacenan en caché (pendiente de implementar en Azure Redis).
    
-   **Minimización de egress:** El retrieval service en GCP evita llamadas innecesarias a Azure OpenAI.
    
-   **Escalado automático:** Cloud Run escala a cero cuando no hay tráfico, reduciendo costos.
    
-   **Monitoreo de costos:** Herramientas nativas de cada proveedor (Azure Cost Management, AWS Cost Explorer, GCP Billing).
    

Para más detalles, consulta [`docs/costos.md`](https://costos.md/).

* * *

## 📚 Documentación Relacionada

-   [README Principal](https://../README.md)
    
-   [Guía de Usuario](https://guia-usuario.md/)
    
-   [Análisis de Costos](https://costos.md/)
    
-   [Reporte RAGAS](https://ragas-report.md/)
    
-   [Patrón de Diseño LLM](https://patron-diseno-llm.md/)
    

* * *

¡Gracias por administrar CODEA RAG! 🚀