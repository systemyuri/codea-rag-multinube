#!/bin/bash
# deploy-retrieval-service.sh - Despliega el servicio de retrieval en Cloud Run
# Uso: ./deploy-retrieval-service.sh <IP_PUBLICA> <PASSWORD>

set -e

# ========== CONFIGURACIÓN ==========
PROJECT_ID="codea-alimentos-minjusdh"   # Cambia si es diferente
REGION="us-central1"
SERVICE_NAME="retrieval-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
# ===================================

# Recibir argumentos (IP y password)
if [ $# -ne 2 ]; then
    echo "❌ Uso: $0 <IP_PUBLICA_ALLOYDB> <CONTRASEÑA_ADMIN>"
    echo "Ejemplo: $0 34.67.89.123 MiClaveSegura123!"
    exit 1
fi

DB_HOST="$1"
DB_PASSWORD="$2"
DB_USER="postgres"
DB_NAME="postgres"
DB_PORT="5432"

echo "=== Despliegue del servicio de retrieval en Cloud Run ==="
echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
echo "Servicio: $SERVICE_NAME"
echo "DB Host: $DB_HOST"

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud no está instalado. Instálalo desde https://cloud.google.com/sdk"
    exit 1
fi

# Configurar proyecto activo
gcloud config set project "$PROJECT_ID"

# Habilitar APIs si es necesario
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Construir y subir imagen
echo "Construyendo y subiendo imagen..."
gcloud builds submit --tag "$IMAGE_NAME" --quiet

# Desplegar en Cloud Run con variables de entorno
echo "Desplegando en Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --timeout 3600 \
    --set-env-vars "DB_HOST=$DB_HOST,DB_PASSWORD=$DB_PASSWORD,DB_USER=$DB_USER,DB_NAME=$DB_NAME,DB_PORT=$DB_PORT" \
    --quiet

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)" --quiet)

echo "✅ Despliegue completado."
echo "🔗 URL del servicio: $SERVICE_URL"
echo "📖 Para probar: curl -X POST $SERVICE_URL/retrieve -H 'Content-Type: application/json' -d '{\"vector\": [0.0]*1536, \"limit\": 3}'"