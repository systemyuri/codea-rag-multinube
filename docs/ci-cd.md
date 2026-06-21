# 🔄 CI/CD Multinube – CODEA RAG

## 📌 Resumen

Este documento describe la estrategia de Integración Continua y Despliegue Continuo (CI/CD) para la plataforma CODEA RAG, que abarca los tres proveedores cloud: **Azure**, **AWS** y **GCP**. Se detalla el estado actual de los scripts de despliegue, las mejoras recomendadas, y el diseño de un pipeline completo con GitHub Actions y Terraform como hoja de ruta futura.

---

## 🏗️ Arquitectura de CI/CD

El flujo de CI/CD se organiza en tres capas:

1. **Build:** Compilación y empaquetado de artefactos (imágenes Docker, código Python, frontend).
2. **Deploy:** Despliegue automatizado a cada proveedor cloud.
3. **Test:** Ejecución de pruebas de integración y evaluación RAGAS.

```mermaid
graph LR
    subgraph "GitHub Actions"
        A[Push a main] --> B[Build Docker Images]
        B --> C[Push a Registries]
        C --> D[Deploy a Azure]
        C --> E[Deploy a AWS]
        C --> F[Deploy a GCP]
    end

    subgraph "Azure"
        D --> G[Azure Functions]
        D --> H[Azure Static Web Apps]
    end

    subgraph "AWS"
        E --> I[AWS Lambda]
        E --> J[S3 Bucket]
    end

    subgraph "GCP"
        F --> K[Cloud Run]
        F --> L[AlloyDB]
    end
```

## 🔧 Estado Actual: Scripts de Despliegue

Actualmente, cada componente se despliega mediante scripts manuales o semiautomatizados:

| Componente | Script | Ubicación | Proveedor |
| --- | --- | --- | --- |
| **Azure Function** | `deploy-azure-function.sh` / `.ps1` | `azure-function/` | Azure |
| **AWS Lambda** | `deploy-aws-ingesta.sh` | `aws-lambda-ingesta/` | AWS |
| **Chunking Service** | Comandos `gcloud` (documentados) | `gcp-services/chunking-service/` | GCP |
| **Retrieval Service** | Comandos `gcloud` (documentados) | `gcp-services/retrieval-service/` | GCP |
| **Frontend** | `deploy.sh` (npm + SWA) | `frontend/` | Azure |

### Fortalezas

-   ✅ Automatización de creación de recursos (grupos, buckets, roles).
    
-   ✅ Manejo de errores básico (`set -e`).
    
-   ✅ Configuración de variables de entorno en los servicios.
    
-   ✅ Incluyen tips y recomendaciones para troubleshooting.
    

### Debilidades identificadas

| Script | Problema | Impacto |
| --- | --- | --- |
| `deploy-azure-function.sh` | Secretos hardcodeados (ej. `AZURE_OPENAI_KEY`, `DB_PASSWORD`). | Riesgo de exposición en el repositorio. |
| `deploy-aws-ingesta.sh` | Usa `powershell.exe` para empaquetar (no funciona en Linux/macOS). | Falta de portabilidad. |
| `deploy-aws-ingesta.sh` | Secretos hardcodeados. | Mismo riesgo de seguridad. |
| `deploy.sh` | No valida que `DEPLOYMENT_TOKEN` esté definido. | Fallos silenciosos en despliegue. |

* * *

## 🔧 Mejoras Recomendadas para los Scripts Actuales

| Script | Mejora | Justificación |
| --- | --- | --- |
| `deploy-azure-function.sh` | Mover todos los secretos a variables de entorno del sistema (o a GitHub Secrets) y leerlos con `os.environ` o `export` antes de ejecutar. | Seguridad: evitar exponer credenciales en el código. |
| `deploy-aws-ingesta.sh` | 1\. Reemplazar el empaquetado con `powershell.exe` por `zip` nativo o un script Python (`shutil.make_archive`). 2. Mover secretos a variables de entorno. | Portabilidad: que funcione en Linux/macOS. Seguridad: igual que el anterior. |
| `deploy.sh` | Agregar verificación de que `DEPLOYMENT_TOKEN` esté definido antes de ejecutar el despliegue. | Robustez: evitar fallos silenciosos. |

## 🖥️ Ejemplos de Ejecución con Variables de Entorno

### 1. `deploy-azure-function.sh`

**Opción A: Usando `export` antes de ejecutar**
```bash
export AZURE_OPENAI_KEY="tu_clave_real"
export DB_PASSWORD="tu_contraseña_real"
export RETRIEVAL_URL="https://tu-retrieval-service.run.app"
# ... otras variables que quieras sobrescribir
./deploy-azure-function.sh
```

**Opción B: Pasando variables en la misma línea**
```bash
AZURE_OPENAI_KEY="tu_clave" DB_PASSWORD="tu_pass" 
./deploy-azure-function.sh
```

**Opción C: Usando un archivo `.env`**
Crea un archivo `.env` en la misma carpeta:

```bash
# .env
AZURE_OPENAI_KEY=tu_clave
DB_PASSWORD=tu_pass
RETRIEVAL_URL=https://tu-retrieval-service.run.app
```

Luego cárgalo antes de ejecutar:
```bash
source .env
./deploy-azure-function.sh
```

### 2. `deploy.sh` (Frontend)
```bash
export DEPLOYMENT_TOKEN="tu_token_de_azure_static_web_apps"
./deploy.sh
```
O en una línea:
```bash
DEPLOYMENT_TOKEN="tu_token" ./deploy.sh
```

### 3. `deploy-aws-ingesta.sh` (mejorado)
Con la versión mejorada (que te doy abajo), puedes ejecutarlo de forma similar:
```bash
export AWS_ACCESS_KEY_ID="tu_access_key"
export AWS_SECRET_ACCESS_KEY="tu_secret_key"
export DB_PASSWORD="tu_pass"
export AZURE_OPENAI_KEY="tu_clave"
./deploy-aws-ingesta.sh
```

O usando un archivo `.env`:
```bash
source .env
./deploy-aws-ingesta.sh
```


* * *

## 🧪 Ejemplo completo de ejecución con un archivo `.env`

1.  Crea un archivo `.env` en la carpeta `aws-lambda-ingesta`:
```bash
# .env
AWS_ACCESS_KEY_ID=AKIATXZ5M2KIDELBELBN
AWS_SECRET_ACCESS_KEY=tu_secret_key
CHUNKING_URL=https://chunking-service-477131016683.us-central1.run.app
AZURE_OPENAI_ENDPOINT=https://openai-rag-7048.openai.azure.com
AZURE_OPENAI_KEY=4DhrKbT3CsMyi9WEKl178MqI085oNfxXPu3rftVrIDfTvWEokRNpJQQJ99CFACHYHv6XJ3w3AAABACOGmexB
EMBEDDING_DEPLOYMENT=embedding3
DB_HOST=IP_publica_DATA_BASE
DB_PASSWORD=CLAVE_DATA_BASE
DB_USER=postgres
DB_NAME=postgres
DB_PORT=5432
```

2.  Cargar y ejecutar:
```bash
source .env
./deploy-aws-ingesta.sh
```
* * *

## 🚀 Diseño del Pipeline con GitHub Actions

Aunque no está implementado actualmente, se propone el siguiente diseño para un pipeline completo de CI/CD. Los workflows se ejecutarían automáticamente al hacer push a la rama `main` o al crear un release tag.

### 1\. Build y Push de Imágenes Docker
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [chunking-service, retrieval-service]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Login to Google Artifact Registry
        uses: docker/login-action@v2
        with:
          registry: us-central1-docker.pkg.dev
          username: _json_key
          password: ${{ secrets.GCP_SA_KEY }}
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./gcp-services/${{ matrix.service }}
          file: ./gcp-services/${{ matrix.service }}/Dockerfile
          push: true
          tags: |
            us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/codea/${{ matrix.service }}:latest
            us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/codea/${{ matrix.service }}:${{ github.sha }}
```

### 2\. Despliegue a GCP Cloud Run
```yaml
deploy-gcp:
  runs-on: ubuntu-latest
  needs: build
  steps:
    - uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY }}
    - uses: google-github-actions/deploy-cloudrun@v1
      with:
        service: retrieval-service
        image: us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/codea/retrieval-service:latest
        region: us-central1
        env_vars: |
          DB_HOST=${{ secrets.DB_HOST }}
          DB_PASSWORD=${{ secrets.DB_PASSWORD }}
```

### 3\. Despliegue a Azure Functions
```yaml
deploy-azure:
  runs-on: ubuntu-latest
  needs: build
  steps:
    - uses: actions/checkout@v3
    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    - name: Deploy Function App
      run: |
        cd azure-function
        func azure functionapp publish codea-orchestrator --python
```

### 4\. Despliegue a AWS Lambda
```yaml
deploy-aws:
  runs-on: ubuntu-latest
  needs: build
  steps:
    - uses: actions/checkout@v3
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_KEY }}
        aws-region: us-east-1
    - name: Package and deploy Lambda
      run: |
        cd aws-lambda-ingesta
        ./deploy-aws-ingesta.sh
```

### 5\. Despliegue del Frontend (Azure Static Web Apps)
```yaml
deploy-frontend:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Build and deploy
      uses: Azure/static-web-apps-deploy@v1
      with:
        azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_TOKEN }}
        repo_token: ${{ secrets.GITHUB_TOKEN }}
        action: "upload"
        app_location: "/frontend"
        output_location: "dist"
```

### 6\. Pruebas Automatizadas (RAGAS)
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Install dependencies
      run: |
        cd tests/ragas
        pip install -r requirements.txt
    - name: Run RAGAS evaluation
      run: |
        cd tests/ragas
        python evaluate_ragas.py --threshold 0.7
```

* * *

## 🧩 Infraestructura como Código (IaC) con Terraform

Como evolución futura, se propone migrar la gestión de recursos base a Terraform, garantizando reproducibilidad y versionado.

### Estructura de Terraform

```text
terraform/
├── azure/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── aws/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── gcp/
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```
### Ejemplo: Recurso de AlloyDB en GCP (Terraform)

```hcl

\# terraform/gcp/main.tf
resource "google\_alloydb\_cluster" "codea" {
  cluster\_id   \= "codea-cluster"
  location     \= "us-central1"
  network      \= "projects/${var.project\_id}/global/networks/default"
  initial\_user {
    user     \= "postgres"
    password \= var.db\_password
  }
}

resource "google\_alloydb\_instance" "codea" {
  cluster       \= google\_alloydb\_cluster.codea.name
  instance\_id   \= "codea-instance"
  instance\_type \= "PRIMARY"
  machine\_config {
    cpu\_count \= 2
  }
}
```

### Ejemplo: Bucket S3 en AWS (Terraform)

```hcl

\# terraform/aws/main.tf
resource "aws\_s3\_bucket" "codea\_docs" {
  bucket \= "codea-docs-ingesta"
  force\_destroy \= true
}

resource "aws\_s3\_bucket\_notification" "lambda\_trigger" {
  bucket \= aws\_s3\_bucket.codea\_docs.id
  lambda\_function {
    lambda\_function\_arn \= aws\_lambda\_function.ingesta.arn
    events              \= \["s3:ObjectCreated:\*"\]
  }
}
```

* * *

## 🔐 Gestión de Secrets y Variables de Entorno

| Secret | Proveedor | Uso |
| --- | --- | --- |
| `GCP_SA_KEY` | GitHub | Autenticación en GCP (Artifact Registry, Cloud Run) |
| `AZURE_CREDENTIALS` | GitHub | Autenticación en Azure (Functions, Static Web Apps) |
| `AWS_ACCESS_KEY` / `AWS_SECRET_KEY` | GitHub | Autenticación en AWS (Lambda, S3) |
| `DB_HOST`, `DB_PASSWORD` | GitHub | Conexión a AlloyDB (inyectado en GCP y Azure) |
| `AZURE_OPENAI_KEY` | GitHub | Clave de Azure OpenAI (inyectado en Azure) |

Práctica recomendada: Utilizar GitHub Environments para separar variables de desarrollo, staging y producción.

* * *

## 📊 Estrategia de Despliegue

-   **Blue-Green:** Para Cloud Run, se utiliza la estrategia nativa de revisiones, donde la nueva revisión recibe tráfico gradualmente.
-   **Canary:** No implementado, pero se podría añadir con Cloud Run traffic splitting.
-   **Rollback:** En caso de fallo, se puede revertir a la revisión anterior con `gcloud run services update --revision`.
    

* * *

## 🗺️ Hoja de Ruta de Implementación

| Fase | Acciones | Plazo |
| --- | --- | --- |
| **Fase 1** | Aplicar mejoras de seguridad y portabilidad a los scripts actuales. | Corto plazo (1 semana) |
| **Fase 2** | Crear workflows de GitHub Actions que ejecuten los scripts mejorados. | Medio plazo (2-3 semanas) |
| **Fase 3** | Migrar a Terraform para IaC y añadir despliegues blue-green/canary. | Largo plazo (1-2 meses) |

* * *

## 📚 Documentación Relacionada

-   [Guía de Administrador](https://guia-administrador.md/) – Despliegue manual.
-   [Contenerización](https://contenizacion.md/) – Dockerfiles y buenas prácticas.
-   [README Principal](https://../README.md) – Visión general del proyecto.
    

* * *

Autor: David Yurvilca  
Fecha: Junio 2026  
Versión: 2.0 (actualizada con mejoras y hoja de ruta)