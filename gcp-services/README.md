# GCP Services – Chunking y Retrieval

Este directorio contiene los microservicios desplegados en Google Cloud Run para el sistema RAG CODEA.

## Servicios incluidos

- **Chunking Service**: Divide el texto en fragmentos semánticos.
- **Retrieval Service**: Busca fragmentos similares en AlloyDB usando pgvector.

## Requisitos previos

- Cuenta de GCP con facturación habilitada.
- APIs de Cloud Run y Cloud Build activadas.
- AlloyDB con pgvector y tablas creadas (ver `sql/` en la raíz).

## Despliegue

Cada servicio tiene su propio script de despliegue:

```bash
cd chunking-service && ./deploy-chunking-service.sh
cd retrieval-service && ./deploy-retrieval-service.sh <DB_HOST> <DB_PASSWORD>