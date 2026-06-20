# azure-function

## 📌 Finalidad

Este componente contiene el **orquestador principal** del sistema RAG, implementado como una **Azure Function** en Python. Es el punto de entrada para las consultas de los usuarios y la administración de documentos.

**Responsabilidades**:
- **`/ask`**: Recibe preguntas del frontend, orquesta el flujo RAG completo:
  1. Genera embedding de la pregunta (Azure OpenAI).
  2. Consulta el servicio de retrieval en GCP para obtener fragmentos similares.
  3. Construye un prompt con los fragmentos.
  4. Obtiene la respuesta del modelo de chat (Azure OpenAI).
  5. Devuelve la respuesta al frontend.
- **`/login`**: Autentica al administrador (JWT) y devuelve un token.
- **`/documents`**: Lista los documentos subidos (requiere token).
- **`/documents/delete`**: Elimina un documento (requiere token).
- **`/documents/download`**: Genera una URL prefirmada de S3 para descargar un documento (requiere token).
- **`/upload`**: Recibe un PDF, lo sube a S3 y registra en AlloyDB (requiere token).

---

## 📁 Estructura del directorio

```bash
azure-function/
├── function_app.py # Código principal (modelo de programación v2)
├── host.json # Configuración de la Function App (extensiones, logging)
├── requirements.txt # Dependencias Python
├── local.settings.json # (No subir a Git) Configuración local para desarrollo
└── deploy-azure-function.sh # Script de despliegue automatizado (opcional)
```


### Descripción de archivos

| Archivo | Propósito |
|---------|-----------|
| `function_app.py` | Contiene todas las funciones (endpoints) usando el decorador `@app.route`. Incluye la lógica de embedding, retrieval, chat, autenticación, gestión de documentos y subida a S3. |
| `host.json` | Configuración global de la Function App (versión del bundle de extensiones, logging, etc.). |
| `requirements.txt` | Dependencias: `azure-functions`, `requests`, `PyJWT`, `psycopg2-binary`, `boto3`. |
| `local.settings.json` | **No subir a Git**. Contiene variables de entorno para pruebas locales (claves de OpenAI, URLs, etc.). |
| `deploy-azure-function.sh` | Script bash que automatiza la creación de recursos, configuración de variables y publicación del código. |

> **Nota**: Este proyecto usa el **modelo de programación v2** de Azure Functions (Python), que utiliza `function_app.py` como punto de entrada. No se usan los archivos `__init__.py` ni `function.json` (modelo antiguo).

---

## ✅ Requisitos previos

### Cuentas y permisos
- **Microsoft Azure**: Cuenta con suscripción activa (pago por uso o créditos gratuitos).
- **Azure OpenAI**: Recurso desplegado con modelos de embeddings (`text-embedding-3-small`) y chat (`gpt-4o` o `gpt-35-turbo`).
- **AWS**: Credenciales para acceder a S3 (Access Key, Secret Key).
- **GCP**: Instancia AlloyDB con las tablas `chunks` y `documentos_metadata` (ver scripts en `sql/`).

### Herramientas instaladas
- **Azure CLI** (`az`) – configurado con `az login`.
- **Azure Functions Core Tools** (`func`) – versión 4.x.
- **Python 3.11** (o la versión que uses) y `pip`.
- **Git Bash** (Windows) o **Bash** (Linux/Mac) para ejecutar el script de despliegue.

---

## 🧩 Variables de entorno

La Function App necesita las siguientes variables de entorno (configuradas en Azure o en `local.settings.json` para desarrollo local).

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint de Azure OpenAI. | `https://openai-rag-7048.openai.azure.com` |
| `AZURE_OPENAI_KEY` | Clave API de Azure OpenAI. | `4Dhr...` |
| `EMBEDDING_DEPLOYMENT` | Nombre del deployment de embeddings. | `embedding3` |
| `CHAT_DEPLOYMENT` | Nombre del deployment de chat. | `gpt4o` |
| `RETRIEVAL_URL` | URL del servicio de retrieval en GCP Cloud Run. | `https://retrieval-service-...run.app` |
| `ADMIN_USER` | Usuario del panel de administración. | `admin` |
| `ADMIN_PASS` | Contraseña del panel de administración. | `ArquitecturaIA-2026` |
| `JWT_SECRET` | Secreto para firmar los tokens JWT. | `D3M0S14R4G` |
| `TOKEN_EXPIRY_MINUTES` | Tiempo de expiración del token (minutos). | `60` |
| `AWS_ACCESS_KEY` | Access Key de AWS (para S3). | `AKIATXZ5M2KIDELBELBN` |
| `AWS_SECRET_KEY` | Secret Key de AWS. | `...` |
| `AWS_REGION` | Región de AWS. | `us-east-1` |
| `S3_BUCKET` | Nombre del bucket S3 para documentos. | `codea-docs-ingesta` |
| `DB_HOST` | IP pública de AlloyDB. | `35.202.6.109` |
| `DB_PASSWORD` | Contraseña del usuario `postgres`. | `Yuri123$` |
| `DB_USER` | Usuario de AlloyDB. | `postgres` |
| `DB_NAME` | Nombre de la base de datos. | `postgres` |
| `DB_PORT` | Puerto de AlloyDB. | `5432` |

---

## 🚀 Despliegue

### Automático (recomendado)

El script `deploy-azure-function.sh` automatiza la creación de recursos, configuración de variables y publicación del código.

```bash
cd azure-function
chmod +x deploy-azure-function.sh
./deploy-azure-function.sh
```

### Qué hace el script:

1.  Verifica que `az`, `func` y `python` estén instalados.
    
2.  Inicia sesión en Azure (si no está autenticado).
    
3.  Crea el grupo de recursos, la Storage Account y la Function App (si no existen).
    
4.  Configura todas las variables de entorno.
    
5.  Publica el código con `func azure functionapp publish`.

## 🧪 Pruebas

### Probar el endpoint `/ask` con `curl`

Obtén la clave de función (si usas `auth_level=FUNCTION`):

```bash

az functionapp function keys list --name codea-orchestrator --resource-group codea-rg --function-name ask --query "default" --output tsv
```

Luego prueba:

```bash

curl -X POST "https://codea-orchestrator.azurewebsites.net/api/ask?code=<KEY>" \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Qué órgano administra el REDAM?"}'
```

### Probar el login (para obtener token JWT)

```bash

curl -X POST "https://codea-orchestrator.azurewebsites.net/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ArquitecturaIA-2026"}'

### Ver logs en tiempo real

```bash

az webapp log tail --name codea-orchestrator --resource-group codea-rg
```
* * *

## 🔧 Actualización y mantenimiento

### Actualizar el código

1.  Modifica `function_app.py` (o cualquier otro archivo).
    
2.  Vuelve a ejecutar el script de despliegue o publica manualmente:
    
```bash
func azure functionapp publish codea-orchestrator --python
```

### Actualizar variables de entorno

Puedes cambiar una variable específica sin volver a desplegar:
```bash
az functionapp config appsettings set --name codea-orchestrator --resource-group codea-rg --settings "NUEVA_VAR=valor"
```
### Configurar CORS para el frontend

Si el frontend (Static Web App) necesita comunicarse con la Function App:

```bash
az functionapp cors add --name codea-orchestrator --resource-group codea-rg --allowed-origins "https://codea-frontend.azurestaticapps.net"
```
### Escalar la Function App (si es necesario)

El plan de consumo escala automáticamente. Si necesitas más rendimiento, puedes cambiar a un plan de App Service dedicado.

* * *

## 🔍 Solución de problemas

### 1\. Error `ModuleNotFoundError` al publicar

Causa: Dependencias no instaladas en el entorno de Azure.  
Solución: Asegúrate de que `requirements.txt` contenga todas las dependencias y que la publicación incluya el flag `--python` (para que Azure instale las dependencias automáticamente).

### 2\. Error de autenticación en OpenAI (401)

Causa: La clave de API o el endpoint son incorrectos.  
Solución: Verifica `AZURE_OPENAI_ENDPOINT` y `AZURE_OPENAI_KEY` en las variables de entorno.

### 3\. Timeout al llamar al retrieval service

Causa: El servicio de retrieval tarda más de 30 segundos.  
Solución: Aumenta el timeout en la petición (`retrieve_context` tiene `timeout=30`; puedes subirlo a 60 o más).

### 4\. Error "No se encontró información" en las respuestas

Causa: El retrieval no devuelve chunks porque la base de datos está vacía o el vector no es similar.  
Solución: Verifica que haya documentos en `chunks` y que el embedding de la pregunta sea correcto. Prueba con `limit=20` para aumentar el número de fragmentos recuperados.

### 5\. CORS bloquea las peticiones desde el frontend

Causa: La Function App no permite el origen del frontend.  
Solución: Agrega la URL de la Static Web App a las `allowed-origins` de CORS (ver comando arriba).

* * *

## 📌 Notas adicionales

-   Modelo de programación: Este proyecto usa el modelo v2 (Python) con `function_app.py`. No uses `__init__.py` ni `function.json`.
    
-   Autenticación: Los endpoints de administración (`/documents`, `/upload`, etc.) usan JWT, no la clave de función. El endpoint `/ask` usa la clave de función (por simplicidad).
    
-   Seguridad: Guarda las claves de API y contraseñas en Azure Key Vault para producción.
    
-   Monitoreo: Application Insights está habilitado por defecto (si se creó con el flag correspondiente). Puedes ver métricas y logs desde el portal de Azure.
    

* * *

## 🤝 Contribuciones

Si encuentras un problema o deseas mejorar la Function, abre un pull request o un issue en el repositorio principal.

* * *
Desarrollado por [David Yurivilca](https://github.com/systemyuri) – Proyecto CODEA RAG.
* * *