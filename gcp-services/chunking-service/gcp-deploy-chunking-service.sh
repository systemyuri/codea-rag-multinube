#!/bin/bash
# deploy-chunking-service.sh - Despliega el servicio de chunking en Cloud Run

set -e  # Detener si hay error

# ========== CONFIGURACIÓN ==========
PROJECT_ID="codea-alimentos-minjusdh"       # Cambia si es diferente
REGION="us-central1"
SERVICE_NAME="chunking-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
# ===================================

echo "=== Despliegue del servicio de chunking en Cloud Run ==="
echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
echo "Servicio: $SERVICE_NAME"
echo "Imagen: $IMAGE_NAME"

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud no está instalado. Instálalo desde https://cloud.google.com/sdk"
    exit 1
fi

# Configurar proyecto activo
echo "Configurando proyecto activo..."
gcloud config set project "$PROJECT_ID"

# Habilitar APIs necesarias (si no lo están)
echo "Habilitando APIs necesarias..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Construir y subir imagen usando Cloud Build (evita problemas de red local)
echo "Construyendo y subiendo imagen a Google Container Registry..."
gcloud builds submit --tag "$IMAGE_NAME" --quiet

# Desplegar en Cloud Run (crea o actualiza)
echo "Desplegando en Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --timeout 3600 \
    --quiet

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)" --quiet)

echo "✅ Despliegue completado."
echo "🔗 URL del servicio: $SERVICE_URL"
echo "📖 Para probar: curl -X POST $SERVICE_URL/chunk -H 'Content-Type: application/json' -d '{\"text\": \"Artículo 1. Prueba\", \"source\": \"test.pdf\"}'"