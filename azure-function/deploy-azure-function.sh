#!/bin/bash
# deploy-azure-function.sh – Despliegue automático de la Azure Function (orquestador) para CODEA RAG
# Compatible con Linux, macOS y Git Bash (Windows)

set -e  # Detener ejecución si hay error

# ============================================================================
# CONFIGURACIÓN (modifica según tu entorno)
# ============================================================================
# --- Recursos Azure ---
RESOURCE_GROUP="codea-rg"
LOCATION="eastus"
FUNCTION_APP_NAME="codea-orchestrator"
STORAGE_ACCOUNT="codeastorage2026"
PYTHON_VERSION="3.11"
FUNCTIONS_VERSION="4"
OS_TYPE="Linux"

# --- Variables de entorno para la Function App (deben coincidir con tu configuración) ---
AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-https://openai-rag-7048.openai.azure.com}"
AZURE_OPENAI_KEY="${AZURE_OPENAI_KEY:-4DhrKbT3CsMyi9WEKl178MqI085oNfxXPu3rftVrIDfTvWEokRNpJQQJ99CFACHYHv6XJ3w3AAABACOGmexB}"
EMBEDDING_DEPLOYMENT="embedding3"
CHAT_DEPLOYMENT="gpt4o"
RETRIEVAL_URL="${RETRIEVAL_URL:-https://retrieval-service-flzlnepzjq-uc.a.run.app}"

ADMIN_USER="admin"
ADMIN_PASS="ArquitecturaIA-2026"
JWT_SECRET="${JWT_SECRET:-D3M0S14R4G}"
TOKEN_EXPIRY_MINUTES=60

AWS_ACCESS_KEY="${AWS_ACCESS_KEY:-AKIATXZ5M2KIDELBELBN}"
AWS_SECRET_KEY="${AWS_SECRET_KEY:-<TU_SECRET_KEY>}"   # ¡CAMBIA ESTO!
AWS_REGION="us-east-1"
S3_BUCKET="codea-docs-ingesta"

DB_HOST="${DB_HOST:-35.202.6.109}"
DB_PASSWORD="${DB_PASSWORD:-Yuri123$}"
DB_USER="postgres"
DB_NAME="postgres"
DB_PORT="5432"
# ============================================================================

# Colores para mensajes
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}==>${NC} $1"; }

# ============================================================================
# VERIFICACIONES INICIALES
# ============================================================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Despliegue de Azure Function (CODEA Orquestador)${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Verificar que estamos en la carpeta correcta
if [ ! -f "function_app.py" ] && [ ! -f "__init__.py" ]; then
    print_error "No se encuentra function_app.py o __init__.py en el directorio actual."
    print_warn "Asegúrate de ejecutar este script desde la carpeta raíz de la Azure Function."
    exit 1
fi

# 2. Verificar herramientas instaladas
print_step "Verificando herramientas..."

if ! command -v az &> /dev/null; then
    print_error "Azure CLI no está instalado."
    print_warn "Instálalo desde https://docs.microsoft.com/azure/cli/install-azure-cli"
    exit 1
fi

if ! command -v func &> /dev/null; then
    print_error "Azure Functions Core Tools no está instalado."
    print_warn "Instálalo con: npm install -g azure-functions-core-tools@4 --unsafe-perm true"
    exit 1
fi

if ! command -v python &> /dev/null; then
    print_error "Python no está instalado."
    print_warn "Instala Python 3.11 o superior."
    exit 1
fi

print_info "✅ Herramientas verificadas."

# 3. Verificar sesión de Azure
print_step "Verificando sesión de Azure..."
az account show &> /dev/null || {
    print_warn "No has iniciado sesión en Azure. Ejecutando 'az login'..."
    az login
}
print_info "✅ Sesión de Azure activa."

# 4. Verificar que el archivo requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    print_warn "No se encuentra requirements.txt. Creando uno básico..."
    cat > requirements.txt <<EOF
azure-functions
requests
PyJWT
psycopg2-binary
boto3
EOF
    print_info "✅ requirements.txt creado."
fi

# ============================================================================
# CREAR RECURSOS EN AZURE
# ============================================================================
print_step "Creando/verificando recursos en Azure..."

# 4.1 Grupo de recursos
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Creando grupo de recursos '$RESOURCE_GROUP' en '$LOCATION'..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
else
    print_info "Grupo de recursos '$RESOURCE_GROUP' ya existe."
fi

# 4.2 Storage Account
if ! az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Creando Storage Account '$STORAGE_ACCOUNT'..."
    az storage account create --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" --location "$LOCATION" --sku Standard_LRS
else
    print_info "Storage Account '$STORAGE_ACCOUNT' ya existe."
fi

# 4.3 Function App
if ! az functionapp show --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Creando Function App '$FUNCTION_APP_NAME' (Consumption Plan, Linux, Python $PYTHON_VERSION)..."
    az functionapp create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$FUNCTION_APP_NAME" \
        --storage-account "$STORAGE_ACCOUNT" \
        --runtime python \
        --runtime-version "$PYTHON_VERSION" \
        --functions-version "$FUNCTIONS_VERSION" \
        --consumption-plan-location "$LOCATION" \
        --os-type "$OS_TYPE"
else
    print_info "Function App '$FUNCTION_APP_NAME' ya existe."
fi

# ============================================================================
# CONFIGURAR VARIABLES DE ENTORNO
# ============================================================================
print_step "Configurando variables de entorno en Azure..."
az functionapp config appsettings set --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" --settings \
    "AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT" \
    "AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY" \
    "EMBEDDING_DEPLOYMENT=$EMBEDDING_DEPLOYMENT" \
    "CHAT_DEPLOYMENT=$CHAT_DEPLOYMENT" \
    "RETRIEVAL_URL=$RETRIEVAL_URL" \
    "ADMIN_USER=$ADMIN_USER" \
    "ADMIN_PASS=$ADMIN_PASS" \
    "JWT_SECRET=$JWT_SECRET" \
    "TOKEN_EXPIRY_MINUTES=$TOKEN_EXPIRY_MINUTES" \
    "AWS_ACCESS_KEY=$AWS_ACCESS_KEY" \
    "AWS_SECRET_KEY=$AWS_SECRET_KEY" \
    "AWS_REGION=$AWS_REGION" \
    "S3_BUCKET=$S3_BUCKET" \
    "DB_HOST=$DB_HOST" \
    "DB_PASSWORD=$DB_PASSWORD" \
    "DB_USER=$DB_USER" \
    "DB_NAME=$DB_NAME" \
    "DB_PORT=$DB_PORT"

print_info "✅ Variables de entorno configuradas."

# ============================================================================
# PUBLICAR EL CÓDIGO DE LA FUNCIÓN
# ============================================================================
print_step "Publicando el código de la Function App..."

# 5.1 Verificar si hay un entorno virtual local (recomendado)
if [ -d "venv" ]; then
    print_info "Activando entorno virtual..."
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
fi

# 5.2 Instalar dependencias localmente (si no están)
if [ ! -d ".python_packages" ] && [ ! -d "venv" ]; then
    print_info "Instalando dependencias localmente..."
    pip install -r requirements.txt
fi

# 5.3 Publicar con Azure Functions Core Tools
print_info "Ejecutando 'func azure functionapp publish'..."
func azure functionapp publish "$FUNCTION_APP_NAME" --python

# ============================================================================
# FINALIZACIÓN
# ============================================================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Despliegue completado exitosamente${NC}"
echo -e "${GREEN}🌐 URL de la Function App:${NC}"
echo -e "   https://$FUNCTION_APP_NAME.azurewebsites.net"
echo -e "${GREEN}📝 Endpoint de prueba:${NC}"
echo -e "   https://$FUNCTION_APP_NAME.azurewebsites.net/api/ask?code=<FUNCTION_KEY>"
echo -e "${GREEN}========================================${NC}"

# Mostrar cómo obtener la clave de función
echo ""
echo -e "${YELLOW}📌 Para obtener la clave de función, ejecuta:${NC}"
echo "   az functionapp function keys list --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --function-name ask"
echo ""
echo -e "${YELLOW}📌 Para ver los logs en tiempo real:${NC}"
echo "   az webapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"