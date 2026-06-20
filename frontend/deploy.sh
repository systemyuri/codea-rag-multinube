#!/bin/bash
set -e

echo "=== 1. Instalando dependencias ==="
npm install

echo "=== 2. Compilando ==="
npm run build

echo "=== 3. Desplegando ==="
if [ -n "$DEPLOYMENT_TOKEN" ]; then
    npx swa deploy ./dist --env production --deployment-token "$DEPLOYMENT_TOKEN"
else
    az staticwebapp app deploy --name codea-frontend --resource-group codea-rg --source ./dist
fi

echo "✅ Despliegue completado."