# deploy-azure-function.ps1
param(
    [string]$ResourceGroup = "codea-rg",
    [string]$Location = "eastus",
    [string]$FunctionAppName = "codea-orchestrator",
    [string]$StorageAccount = "codeastorage2026",
    [string]$PythonVersion = "3.11",
    [string]$FunctionsVersion = "4",
    [string]$OsType = "Linux"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 Despliegue de Azure Function (CODEA Orquestador)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Verificar herramientas
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI no está instalado." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure Functions Core Tools no está instalado." -ForegroundColor Red
    exit 1
}

# Verificar sesión
az account show 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "🔑 Iniciando sesión en Azure..." -ForegroundColor Yellow
    az login
}

# Crear recursos
Write-Host "📦 Creando/verificando recursos en Azure..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location | Out-Null
az storage account create --name $StorageAccount --resource-group $ResourceGroup --location $Location --sku Standard_LRS | Out-Null
az functionapp create --resource-group $ResourceGroup --name $FunctionAppName --storage-account $StorageAccount --runtime python --runtime-version $PythonVersion --functions-version $FunctionsVersion --consumption-plan-location $Location --os-type $OsType | Out-Null

# Configurar variables de entorno (ajustar valores según tu configuración)
Write-Host "⚙️ Configurando variables de entorno..." -ForegroundColor Yellow
$settings = @(
    "AZURE_OPENAI_ENDPOINT=https://openai-rag-7048.openai.azure.com",
    "AZURE_OPENAI_KEY=4DhrKbT3CsMyi9WEKl178MqI085oNfxXPu3rftVrIDfTvWEokRNpJQQJ99CFACHYHv6XJ3w3AAABACOGmexB",
    "EMBEDDING_DEPLOYMENT=embedding3",
    "CHAT_DEPLOYMENT=gpt4o",
    "RETRIEVAL_URL=https://retrieval-service-flzlnepzjq-uc.a.run.app",
    "ADMIN_USER=admin",
    "ADMIN_PASS=ArquitecturaIA-2026",
    "JWT_SECRET=D3M0S14R4G",
    "TOKEN_EXPIRY_MINUTES=60",
    "AWS_ACCESS_KEY=AKIATXZ5M2KIDELBELBN",
    "AWS_SECRET_KEY=TU_SECRET_KEY",
    "AWS_REGION=us-east-1",
    "S3_BUCKET=codea-docs-ingesta",
    "DB_HOST=35.202.6.109",
    "DB_PASSWORD=Yuri123$",
    "DB_USER=postgres",
    "DB_NAME=postgres",
    "DB_PORT=5432"
)
az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings $settings | Out-Null

# Publicar
Write-Host "📤 Publicando código..." -ForegroundColor Yellow
func azure functionapp publish $FunctionAppName --python

Write-Host "✅ Despliegue completado exitosamente" -ForegroundColor Green
Write-Host "🌐 URL: https://$FunctionAppName.azurewebsites.net"