#!/bin/bash
# ==============================================================================
# Script de despliegue automático de Lambda de ingesta en AWS
# 
# Requisitos previos (leer antes de ejecutar):
#   1. Tener instalado AWS CLI (https://aws.amazon.com/cli/) y configurado (aws configure)
#   2. Tener instalado Python 3.11+ y pip
#   3. Tener los siguientes archivos en el mismo directorio:
#        - lambda_function.py   (código de la Lambda)
#        - requirements.txt     (pypdf, requests, psycopg2-binary)
#        - trust-policy.json    (política de confianza para Lambda)
#   4. Conocer la IP pública de AlloyDB (ejecuta: 
#        gcloud alloydb instances describe codea-instance --cluster=codea-cluster --region=us-central1 --format="value(publicIpAddress)")
#   5. Tener las credenciales de Azure OpenAI (endpoint, clave, deployment de embeddings)
#   6. Tener el servicio de chunking desplegado en Cloud Run y su URL pública
#
# Recomendaciones y tips ante problemas:
#   - Si falla por rate limit (429) en Azure OpenAI: aumentar cuotas, implementar backoff (ya incluido en código) o usar batch embeddings.
#   - Si la Lambda no se conecta a AlloyDB: verificar IP pública, regla de firewall (autorizar 0.0.0.0/0 temporalmente), y que la instancia esté activa.
#   - Si el bucket S3 no dispara la Lambda: revisar que la notificación esté configurada (el script lo hace) y que la Lambda tenga permiso para ejecutarse.
#   - Si el ZIP es muy grande: excluir archivos innecesarios (__pycache__, *.pyc).
#   - Para depurar: usar `aws logs tail /aws/lambda/codea-ingesta --follow` después de subir un PDF.
# ==============================================================================

set -e  # Detener si hay error

# ==================== CONFIGURACIÓN INICIAL ====================
# --- Recursos AWS ---
BUCKET_NAME="codea-docs-ingesta"
FUNCTION_NAME="codea-ingesta"
REGION="us-east-1"
ROLE_NAME="codea-ingesta-role"
POLICY_NAME="codea-s3-read-policy"
LAMBDA_HANDLER="lambda_function.lambda_handler"
RUNTIME="python3.11"
TIMEOUT=300          # segundos
MEMORY=512           # MB

# --- URLs y endpoints de servicios externos ---
CHUNKING_URL="https://chunking-service-477131016683.us-central1.run.app"
AZURE_OPENAI_ENDPOINT="https://openai-rag-7048.openai.azure.com"
AZURE_OPENAI_KEY="${AZURE_OPENAI_KEY:-4DhrKbT3CsMyi9WEKl178MqI085oNfxXPu3rftVrIDfTvWEokRNpJQQJ99CFACHYHv6XJ3w3AAABACOGmexB}"
EMBEDDING_DEPLOYMENT="embedding3"

# --- AlloyDB (GCP) ---
DB_HOST="35.202.6.109"        # IP pública de tu instancia AlloyDB (verificar con gcloud)
DB_PASSWORD="Yuri123$"        # Contraseña del usuario postgres
DB_USER="postgres"
DB_NAME="postgres"
DB_PORT="5432"
# ===============================================================

# Verificar requisitos mínimos
echo "=== Verificando requisitos previos ==="
command -v aws >/dev/null 2>&1 || { echo "❌ aws CLI no instalada. Instala desde https://aws.amazon.com/cli/"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "❌ pip no instalado. Instala Python y pip."; exit 1; }
command -v python >/dev/null 2>&1 || { echo "❌ python no instalado. Se requiere Python 3.11+."; exit 1; }
if [ ! -f "lambda_function.py" ]; then echo "❌ No se encuentra lambda_function.py en el directorio actual."; exit 1; fi
if [ ! -f "requirements.txt" ]; then echo "❌ No se encuentra requirements.txt."; exit 1; fi
if [ ! -f "trust-policy.json" ]; then echo "❌ No se encuentra trust-policy.json."; exit 1; fi

echo "✅ Requisitos cumplidos."

echo "=== Despliegue de infraestructura AWS para Lambda de ingesta ==="

# 1. Crear bucket S3 (si no existe)
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Creando bucket S3..."
    aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
else
    echo "Bucket ya existe."
fi

# 2. Crear rol IAM (si no existe)
if ! aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "Creando rol IAM..."
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file://trust-policy.json
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
else
    echo "Rol IAM ya existe."
fi

# 3. Crear política personalizada para S3 (si no existe)
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)
if [ -z "$POLICY_ARN" ]; then
    echo "Creando política S3..."
    cat > s3-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::$BUCKET_NAME",
                "arn:aws:s3:::$BUCKET_NAME/*"
            ]
        }
    ]
}
EOF
    POLICY_ARN=$(aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file://s3-policy.json --query "Policy.Arn" --output text)
    rm s3-policy.json
else
    echo "Política S3 ya existe."
fi
aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "$POLICY_ARN"

# 4. Empaquetar código Lambda (CORREGIDO: lambda_function.py en la raíz del ZIP)
echo "Preparando paquete de Lambda..."
rm -rf package lambda-deployment.zip
mkdir package
pip install --target ./package --platform manylinux2014_x86_64 --python-version 3.11 --only-binary=:all: -r requirements.txt
cp lambda_function.py package/

# Comprimir el contenido de package (sin incluir la carpeta package)
cd package
powershell.exe -Command "Compress-Archive -Path * -DestinationPath ../lambda-deployment.zip -Force"
cd ..

# Verificar que lambda_function.py esté en la raíz del ZIP
echo "Verificando contenido del ZIP..."
if powershell.exe -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::OpenRead('lambda-deployment.zip').Entries | ForEach-Object { if (\$_.FullName -eq 'lambda_function.py') { exit 0 } }"; then
    echo "✅ lambda_function.py encontrado en la raíz del ZIP."
else
    echo "❌ ERROR: lambda_function.py NO se encuentra en la raíz del ZIP. Abortando despliegue."
    exit 1
fi

# 5. Crear o actualizar función Lambda
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query "Role.Arn" --output text)
if aws lambda get-function --function-name "$FUNCTION_NAME" 2>/dev/null; then
    echo "Actualizando código de Lambda existente..."
    aws lambda update-function-code --function-name "$FUNCTION_NAME" --zip-file fileb://lambda-deployment.zip
    echo "Esperando 10 segundos a que se complete la actualización..."
    sleep 10
else
    echo "Creando nueva función Lambda..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$LAMBDA_HANDLER" \
        --zip-file fileb://lambda-deployment.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY"
fi

# 6. Configurar variables de entorno
echo "Configurando variables de entorno..."
cat > env.json <<EOF
{
  "Variables": {
    "CHUNKING_URL": "$CHUNKING_URL",
    "AZURE_OPENAI_ENDPOINT": "$AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY": "$AZURE_OPENAI_KEY",
    "EMBEDDING_DEPLOYMENT": "$EMBEDDING_DEPLOYMENT",
    "DB_HOST": "$DB_HOST",
    "DB_PASSWORD": "$DB_PASSWORD",
    "DB_USER": "$DB_USER",
    "DB_NAME": "$DB_NAME",
    "DB_PORT": "$DB_PORT"
  }
}
EOF
aws lambda update-function-configuration --function-name "$FUNCTION_NAME" --environment file://env.json

# 7. Agregar permiso para S3 (si no existe)
echo "Configurando permiso para S3..."
aws lambda add-permission --function-name "$FUNCTION_NAME" --statement-id s3-invoke --action lambda:InvokeFunction --principal s3.amazonaws.com --source-arn "arn:aws:s3:::$BUCKET_NAME" 2>/dev/null || echo "Permiso ya existe."

# 8. Configurar notificación S3
echo "Configurando evento S3..."
LAMBDA_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --query "Configuration.FunctionArn" --output text)
cat > notification.json <<EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"]
    }
  ]
}
EOF
aws s3api put-bucket-notification-configuration --bucket "$BUCKET_NAME" --notification-configuration file://notification.json
rm notification.json

echo "✅ Despliegue completado."
echo ""
echo "=== RECOMENDACIONES Y TIPS ==="
echo "1. Prueba la Lambda subiendo un PDF:"
echo "   aws s3 cp ruta/documento.pdf s3://$BUCKET_NAME/"
echo ""
echo "2. Monitorea los logs en tiempo real:"
echo "   aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
echo "3. Si ves errores 429 (Too Many Requests) en Azure OpenAI:"
echo "   - Aumenta las cuotas de TPM/RPM en el portal de Azure OpenAI"
echo "   - Añade un sleep entre chunks o implementa batch embeddings (enviar 10 textos de una vez)"
echo "   - El código actual ya tiene reintentos con backoff, pero si persiste, reduce el tamaño de chunk o aumenta la memoria de Lambda."
echo ""
echo "4. Problemas de conexión a AlloyDB:"
echo "   - Verifica que la instencia esté activa (gcloud alloydb instances describe ...)"
echo "   - Comprueba que la IP pública no haya cambiado (actualiza DB_HOST en la configuración del script y vuelve a ejecutar)"
echo "   - Temporalmente, autoriza 0.0.0.0/0 en las redes externas de AlloyDB:"
echo "       gcloud alloydb instances update codea-instance --cluster=codea-cluster --region=us-central1 --authorized-external-networks=0.0.0.0/0"
echo ""
echo "5. Para depurar errores internos de Lambda, mira los logs detallados en CloudWatch:"
echo "   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/$FUNCTION_NAME"
echo ""
echo "6. Si el ZIP es demasiado grande (más de 50 MB), sube el código a S3 y referencia el objeto:"
echo "   aws s3 cp lambda-deployment.zip s3://$BUCKET_NAME/lambda.zip"
echo "   aws lambda update-function-code --function-name $FUNCTION_NAME --s3-bucket $BUCKET_NAME --s3-key lambda.zip"
echo ""
echo "7. Para reducir costos:"
echo "   - Configura expiración de logs en CloudWatch: 7 días"
echo "   - Elimina versiones antiguas de la Lambda si no las necesitas"
echo "   - Detén la instancia de AlloyDB cuando no la uses (el script gcp-codea-deactivate.sh que hicimos)"
echo ""
echo "¡Listo! El sistema de ingesta está operativo."