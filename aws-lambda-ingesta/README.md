# aws-lambda-ingesta

## ?? Finalidad

Este componente implementa la funci車n?AWS Lambda?que automatiza la ingesta y procesamiento de documentos PDF para el sistema RAG?CODEA.

Flujo de trabajo:

1.  Un usuario (o administrador) sube un PDF al bucket S3?`codea-docs-ingesta`.
2.  El evento?`ObjectCreated`?activa la funci車n Lambda.
3.  La Lambda:
    -   Descarga el PDF desde S3.
    -   Extrae el texto usando?`pypdf`.
    -   Llama al servicio de?chunking?(GCP Cloud Run) para dividir el texto en fragmentos sem芍nticos.
    -   Por cada fragmento, genera un?embedding?usando Azure OpenAI.
    -   Guarda el fragmento y su vector en la tabla?`chunks`?de?AlloyDB?(GCP).
    -   Registra el procesamiento en la tabla?`documentos_metadata`?(actualiza el campo?`processed`).

* * *

## ?? Estructura del directorio
```bash
aws-lambda-ingesta/  
念岸岸 lambda\_function.py # C車digo principal de la Lambda  
念岸岸 requirements.txt # Dependencias para el entorno de ejecuci車n  
念岸岸 trust-policy.json # Pol赤tica de confianza para el rol IAM  
弩岸岸 deploy-aws-ingesta.sh # Script de despliegue automatizado
```

### Descripci車n de archivos

| Archivo | Prop車sito |
|---------|-----------|
| `lambda_function.py` | Contiene el handler (`lambda_handler`) y las funciones auxiliares: extracci車n de texto, generaci車n de embeddings, guardado en AlloyDB, etc. |
| `requirements.txt` | Lista de dependencias Python (instaladas durante el despliegue para el entorno Linux de Lambda). |
| `trust-policy.json` | Permite que el servicio `lambda.amazonaws.com` asuma el rol IAM creado. |
| `deploy-aws-ingesta.sh` | Script Bash que automatiza todo el proceso de despliegue: creaci車n de bucket, roles, pol赤ticas, empaquetado, subida de la Lambda y configuraci車n del trigger S3. |


---

## ? Requisitos previos

### Cuentas y permisos
- **AWS**: Cuenta con permisos para crear roles IAM, buckets S3 y funciones Lambda.
- **GCP**: Instancia de AlloyDB con las tablas `chunks` y `documentos_metadata` creadas.
- **Azure**: Recurso de Azure OpenAI con despliegues para embeddings (`text-embedding-3-small`) y chat (opcional para la Lambda, solo usa embeddings).

### Herramientas instaladas
- **AWS CLI** (`aws`) 每 configurado con credenciales v芍lidas.
- **Python 3.11+** y `pip` (para pruebas locales y empaquetado).
- **Git Bash** (Windows) o **Bash** (Linux/Mac) para ejecutar el script.
- **`zip`** (si no est芍 disponible, el script usa PowerShell en Windows).

### Servicios desplegados
- **Chunking Service** (GCP Cloud Run) 每 URL p迆blica donde se env赤a el texto para fragmentar.
- **AlloyDB** (GCP) 每 IP p迆blica, contrase?a y credenciales de acc


## ?? Variables de entorno

La Lambda necesita las siguientes variables de entorno para funcionar. Se configuran autom芍ticamente al ejecutar `deploy-aws-ingesta.sh`, pero puedes revisarlas en el script o modificarlas manualmente.

| Variable | Descripci車n | Ejemplo |
|----------|-------------|---------|
| `CHUNKING_URL` | URL del servicio de chunking en GCP Cloud Run. | `https://chunking-service-...run.app` |
| `AZURE_OPENAI_ENDPOINT` | Endpoint de Azure OpenAI para embeddings. | `https://openai-rag-7048.openai.azure.com` |
| `AZURE_OPENAI_KEY` | Clave API de Azure OpenAI. | `4Dhr...` |
| `EMBEDDING_DEPLOYMENT` | Nombre del deployment de embeddings. | `embedding3` |
| `DB_HOST` | IP p迆blica de la instancia AlloyDB. | `35.202.6.109` |
| `DB_PASSWORD` | Contrase?a del usuario `postgres` en AlloyDB. | `Yuri123$` |
| `DB_USER` | Usuario de AlloyDB (por defecto `postgres`). | `postgres` |
| `DB_NAME` | Nombre de la base de datos. | `postgres` |
| `DB_PORT` | Puerto de AlloyDB. | `5432` |

> **Nota**: `DB_USER`, `DB_NAME` y `DB_PORT` tienen valores por defecto y no es necesario cambiarlos a menos que tu configuraci車n sea diferente.

---

## ?? Despliegue

### Autom芍tico (recomendado)

El script `deploy-aws-ingesta.sh` realiza todas las tareas en un solo paso desde **git bash**:

```bash
cd aws-lambda-ingesta
chmod +x deploy-aws-ingesta.sh
./deploy-aws-ingesta.sh
```

Qu谷 hace el script:

1.  Verifica que?`aws`?CLI,?`pip`?y?`python`?est谷n instalados.
    
2.  Crea el bucket S3 (`codea-docs-ingesta`) si no existe.
    
3.  Crea el rol IAM (`codea-ingesta-role`) con la pol赤tica de confianza.
    
4.  Adjunta la pol赤tica?`AWSLambdaBasicExecutionRole`?(logs en CloudWatch).
    
5.  Crea una pol赤tica personalizada para leer objetos de S3 y la adjunta al rol.
    
6.  Instala las dependencias en una carpeta?`package`?(forzando la plataforma?`manylinux2014_x86_64`?para compatibilidad con Lambda).
    
7.  Copia?`lambda_function.py`?a?`package`?y comprime todo en?`lambda-deployment.zip`.
    
8.  Crea o actualiza la funci車n Lambda con el ZIP y configura el handler (`lambda_function.lambda_handler`).
    
9.  Configura las variables de entorno a partir de los valores definidos en el script.
    
10.  Agrega el permiso a S3 para invocar la Lambda.
     
11.  Configura la notificaci車n S3 para que dispare la Lambda ante eventos?`ObjectCreated`.

## ?? Pruebas

### Subir un PDF de prueba

```bash
aws s3 cp "ruta/al/documento.pdf" s3://codea-docs-ingesta/
```
### Monitorear los logs

```bash
aws logs tail /aws/lambda/codea-ingesta \--follow
```

### Verificar en AlloyDB

```sql
SELECT COUNT(\*) FROM chunks WHERE source LIKE '%documento.pdf%';
SELECT filename, processed FROM documentos\_metadata WHERE filename \= 'documento.pdf';
```


## ?? Actualizaci車n y mantenimiento

### Actualizar el c車digo de la Lambda

1.  Modifica?`lambda_function.py`.
    
2.  Vuelve a ejecutar el script?`deploy-aws-ingesta.sh`?(realizar芍 todo el empaquetado y despliegue autom芍ticamente).
    

### Actualizar variables de entorno

Puedes modificar las variables directamente en el script?`deploy-aws-ingesta.sh`?y volver a ejecutarlo, o usar el comando:

```bash
aws lambda update-function-configuration --function-name codea-ingesta \--environment Variables\={NUEVA\_VAR\=valor}
```

### Cambiar el tama?o de memoria o tiempo de ejecuci車n

Modifica?`TIMEOUT`?y?`MEMORY`?en el script y vuelve a ejecutarlo, o usa:
```bash
aws lambda update-function-configuration --function-name codea-ingesta \--timeout 300 --memory-size 1024
```




## ?? Soluci車n de problemas

### 1\. Error?`Runtime.ImportModuleError: No module named 'lambda_function'`

## 

Causa: El archivo?`lambda_function.py`?no est芍 en la ra赤z del ZIP.  
Soluci車n: Aseg迆rate de que al crear el ZIP, el archivo est谷 en la ra赤z (no dentro de una carpeta?`package`). El script?`deploy-aws-ingesta.sh`?ya lo hace correctamente.

### 2\. Error?`NoSuchKey`?al procesar el PDF

## 

Causa: La clave del objeto S3 contiene caracteres especiales (espacios,?`#`,?`+`) y la Lambda no los decodifica correctamente.  
Soluci車n: En?`lambda_function.py`, usa?`urllib.parse.unquote_plus()`?para decodificar la clave del evento S3.

### 3\. Error de conexi車n a AlloyDB (timeout)

## 

Causa: La IP p迆blica de AlloyDB ha cambiado, o la instancia est芍 detenida.  
Soluci車n:

-   Verifica la IP con?`gcloud alloydb instances describe ...`.
    
-   Actualiza?`DB_HOST`?en las variables de entorno.
    
-   Autoriza?`0.0.0.0/0`?temporalmente para pruebas:
    
    ```bash      
    gcloud alloydb instances update codea-instance \--cluster\=codea-cluster \--region\=us-central1 --authorized-external-networks\=0.0.0.0/0
    ```

### 4\. Error 429 (Rate Limit) en Azure OpenAI

## 

Causa: Demasiadas peticiones de embeddings.  
Soluci車n:

-   Aumenta las cuotas en el portal de Azure OpenAI.
    
-   Reduce el n迆mero de chunks procesados en paralelo (ya tienes backoff exponencial en?`get_embedding`).
    
-   Implementa batch embeddings (enviar varios textos en una sola petici車n).
    



## ?? Contribuciones

Si encuentras un problema o deseas mejorar la funci車n, abre un pull request o un issue en el repositorio principal.

* * *
Desarrollado por?[David Yurivilca](https://github.com/systemyuri)?每 Proyecto CODEA RAG MULTINUBE.


---

## ? ?Qu谷 cubre este README?

| Secci車n | Contenido |
|---------|-----------|
| **Finalidad** | Explica el prop車sito de la Lambda y su flujo de trabajo. |
| **Estructura** | Lista y describe los archivos en la carpeta. |
| **Requisitos** | Cuentas, herramientas y servicios necesarios. |
| **Variables de entorno** | Tabla con todas las variables requeridas. |
| **Despliegue** | Instrucciones autom芍ticas y manuales. |
| **Pruebas** | C車mo probar la Lambda y verificar resultados. |
| **Actualizaci車n** | C車mo modificar el c車digo y las variables. |
| **Solucion de Problemas** | C車mo solucionar problemas comunes. |

---
