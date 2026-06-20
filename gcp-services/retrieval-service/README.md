# retrieval-service

## 📌 Finalidad

Este microservicio, desplegado en **Cloud Run (GCP)**, es el encargado de realizar la búsqueda por similitud semántica en la base de datos vectorial **AlloyDB con pgvector**. Recibe un vector de embedding (generado a partir de la pregunta del usuario) y devuelve los fragmentos de texto más similares almacenados en la tabla `chunks`.

**Flujo de trabajo**:
1. Recibe una petición POST con un vector de 1536 dimensiones (embedding de la pregunta).
2. Ejecuta una consulta SQL en AlloyDB utilizando el operador `<->` de pgvector (distancia coseno).
3. Devuelve los `limit` fragmentos más similares (por defecto 5), ordenados por similitud ascendente.
4. Cada fragmento incluye: `content`, `source`, `article`, `norm_code`, `title` (si están disponibles).


## ✅ Requisitos previos

- **AlloyDB**: La base de datos debe estar configurada con las tablas `chunks` y `documentos_metadata` y la extensión `vector` habilitada. Consulta los scripts en `sql/` para crear la estructura.
---

## 📁 Estructura del directorio


```bash
gcp-services/retrieval-service/
├── app/
│ ├── init.py
│ ├── main.py # Punto de entrada FastAPI
│ ├── retrieval.py # Lógica de conexión a AlloyDB y consulta pgvector
│ └── models.py # Modelos Pydantic para la API
├── Dockerfile # Configuración para construir la imagen
├── requirements.txt # Dependencias Python
└── deploy-retrieval-service.sh # Script de despliegue automatizado
```


### Descripción de archivos

| Archivo | Propósito |
|---------|-----------|
| `app/main.py` | Define los endpoints de la API (`/retrieve`, `/health`) y configura Swagger UI (`/docs`). |
| `app/retrieval.py` | Contiene la lógica de conexión a AlloyDB y la consulta pgvector (orden por distancia coseno). |
| `app/models.py` | Define los modelos de solicitud (`RetrievalRequest`) y respuesta (`RetrievalResponse`, `ChunkResult`). |
| `Dockerfile` | Construye la imagen usando Python 3.11-slim y ejecuta `uvicorn`. |
| `requirements.txt` | Dependencias: `fastapi`, `uvicorn`, `python-multipart`, `psycopg2-binary`, `pydantic`. |
| `deploy-retrieval-service.sh` | Automatiza la construcción, subida a GCR y despliegue en Cloud Run con variables de entorno. |

---

## ✅ Requisitos previos

### Cuentas y permisos
- **GCP**: Proyecto con facturación habilitada, APIs de Cloud Run y Cloud Build activadas.
- **AlloyDB**: Instancia con la extensión `vector` habilitada y la tabla `chunks` creada (con columna `embedding vector(1536)`).
- **Red**: La IP pública de la instancia AlloyDB debe estar autorizada para conexiones desde Cloud Run (o usar VPC Connector).

### Herramientas instaladas
- **Google Cloud SDK (`gcloud`)** – configurado con el proyecto activo.
- **Docker** (opcional, si se construye localmente).
- **Git Bash** (Windows) o **Bash** (Linux/Mac) para ejecutar el script.

---

## 🚀 Despliegue

### Automático (recomendado)

El script `deploy-retrieval-service.sh` realiza todo el proceso en un solo paso, incluyendo la configuración de variables de entorno.

```bash
cd gcp-services/retrieval-service
chmod +x deploy-retrieval-service.sh
./deploy-retrieval-service.sh <IP_PUBLICA_ALLOYDB> <CONTRASEÑA>
```

### Ejemplo:
```bash
./deploy-retrieval-service.sh 35.202.6.109 "Prueba123$"
```

### Que hace el script:
1.  Verifica que `gcloud` esté instalado.
    
2.  Configura el proyecto activo.
    
3.  Habilita las APIs necesarias (`cloudbuild.googleapis.com`, `run.googleapis.com`).
    
4.  Construye la imagen usando Cloud Build.
    
5.  Despliega la imagen en Cloud Run con las variables de entorno:
    
    -   `DB_HOST` = IP de AlloyDB.
        
    -   `DB_PASSWORD` = Contraseña del usuario `postgres`.
        
    -   `DB_USER`, `DB_NAME`, `DB_PORT` (valores por defecto o personalizados).
        
6.  Muestra la URL pública del servicio.


## 🧪 Uso de la API

### Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/retrieve` | Busca fragmentos similares al vector recibido. |
| `GET` | `/health` | Verifica el estado del servicio. |
| `GET` | `/docs` | Interfaz Swagger UI para probar la API. |

### Solicitud (`POST /retrieve`)

```json

{
  "vector": [0.0, 0.0, ...],  // Lista de 1536 floats
  "limit": 5                  // Opcional (por defecto 5)
}
```

Ejemplo con `curl` (vector de ceros, devuelve los primeros 5 registros):

```bash

curl -X POST https://retrieval-service-...run.app/retrieve \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.0]*1536, "limit": 5}'
```


Respuesta:
```json
{
  "chunks": [
    {
      "content": "Artículo 1. Registro de Deudores Alimentarios Morosos...",
      "source": "LEY 28970.pdf",
      "article": "1",
      "norm_code": "LEY 28970",
      "title": "LEY QUE CREA EL REGISTRO DE DEUDORES ALIMENTARIOS MOROSOS"
    },
    {
      "content": "Artículo 481. Los alimentos se regulan por el juez...",
      "source": "CODIGO_CIVIL.pdf",
      "article": "481",
      "norm_code": "DECRETO LEGISLATIVO 295",
      "title": "CODIGO CIVIL"
    }
  ]
}
```

* * *

## 🔧 Configuración y personalización

### Variables de entorno

| Variable | Descripción | Ejemplo |
| --- | --- | --- |
| `DB_HOST` | IP pública de la instancia AlloyDB. | `35.202.6.109` |
| `DB_PASSWORD` | Contraseña del usuario `postgres`. | `Yuri123$` |
| `DB_USER` | Usuario de AlloyDB (por defecto `postgres`). | `postgres` |
| `DB_NAME` | Nombre de la base de datos. | `postgres` |
| `DB_PORT` | Puerto de AlloyDB. | `5432` |

### Parámetros en `retrieval.py`

| Parámetro | Valor | Descripción |
| --- | --- | --- |
| `DEFAULT_LIMIT` | `5` | Número de fragmentos a devolver si no se especifica en la solicitud. |
| `connect_timeout` | `10` | Tiempo de espera para la conexión a la base de datos (segundos). |

### Optimización de consultas pgvector

Para mejorar el rendimiento de la búsqueda, crea un índice HNSW en la tabla `chunks` (ejecutar una sola vez en AlloyDB):
```sql
CREATE INDEX idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
```

Si el tamaño de la tabla es pequeño (menos de 10,000 registros), el índice no es necesario, pero para grandes volúmenes acelera la búsqueda significativamente.


## 🔍 Solución de problemas

### 1\. Error de conexión a AlloyDB (timeout)

Causa: La IP pública de AlloyDB ha cambiado, la instancia está detenida o la red no está autorizada.  
Solución:

-   Verifica la IP con `gcloud alloydb instances describe ...`.
    
-   Asegúrate de que la instancia esté `READY`.
    
-   Autoriza `0.0.0.0/0` temporalmente para pruebas:
    
    ```bash       
    gcloud alloydb instances update codea-instance --cluster=codea-cluster --region=us-central1 --authorized-external-networks=0.0.0.0/0
    ```
    

### 2\. Error de autenticación en AlloyDB (`psycopg2.OperationalError`)

Causa: Contraseña incorrecta o usuario no válido.  
Solución: Verifica `DB_PASSWORD` y `DB_USER` en las variables de entorno.

### 3\. Error `column "embedding" does not exist`

Causa: La tabla `chunks` no tiene la columna `embedding` o la extensión pgvector no está habilitada.  
Solución: Ejecuta en AlloyDB:

```sql

CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding vector(1536);
```

### 4\. Resultados vacíos aunque hay datos en la tabla

Causa: El vector de consulta es muy diferente a todos los vectores almacenados, o la tabla está vacía.  
Solución:

-   Verifica que haya datos en la tabla `chunks` con `SELECT COUNT(*) FROM chunks;`.
    
-   Aumenta el `limit` para ver si aparecen resultados.
    
-   Prueba con un vector de prueba (ceros) para confirmar que la consulta devuelve los primeros registros.
    

### 5\. Error de importación de `psycopg2`

Causa: Dependencia no instalada en el entorno de Cloud Run.  
Solución: Asegúrate de que `psycopg2-binary` esté en `requirements.txt` y que la imagen se construya correctamente.

* * *

## 📌 Notas adicionales

-   Seguridad: El servicio está configurado con `--allow-unauthenticated` para que pueda ser invocado por la Azure Function sin autenticación adicional. Si se requiere mayor seguridad, se puede habilitar la autenticación IAM y configurar la Function para que use credenciales de GCP.
    
-   Escalado: Cloud Run escala automáticamente. El tiempo de inicio de una nueva instancia (cold start) puede ser de unos segundos; para reducir la latencia, considera configurar `--min-instances=1`.
    
-   Monitoreo: Cloud Logging registra todas las solicitudes y errores. Puedes ver los logs con:
    
    ```bash
    
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=retrieval-service" --limit 20
    ```

-   Costos: Cloud Run tiene un nivel gratuito de 2 millones de solicitudes al mes. El costo adicional es mínimo para un uso moderado.

## 🤝 Contribuciones

Si encuentras un problema o deseas mejorar el servicio, abre un pull request o un issue en el repositorio principal.

* * *

Desarrollado por [David Yurivilca](https://github.com/systemyuri) – Proyecto CODEA RAG.



---

## ✅ ¿Qué cubre este README?

| Sección | Contenido |
|---------|-----------|
| **Finalidad** | Explica el propósito del servicio y su flujo de trabajo. |
| **Estructura** | Lista y describe los archivos en la carpeta. |
| **Requisitos** | Cuentas, herramientas y servicios necesarios. |
| **Despliegue** | Instrucciones automáticas y manuales para Cloud Run. |
| **Uso de la API** | Endpoints, ejemplos de solicitud y respuesta. |
| **Configuración** | Variables de entorno y optimización de índices pgvector. |
| **Solución de problemas** | Problemas comunes y soluciones. |

---
