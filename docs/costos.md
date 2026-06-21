# 💰 Optimización de Costos (FinOps) – CODEA RAG

## 📌 Resumen Ejecutivo

Este documento presenta un análisis detallado de los costos operativos de la plataforma CODEA RAG, desglosados por proveedor cloud, por consulta y por token. Se identifican las principales fuentes de gasto y se proponen estrategias de optimización basadas en prácticas FinOps (caching, escalado inteligente, minimización de egress). El objetivo es mantener el sistema operativo con un costo mensual estimado de **~$150‑$200 USD** para un volumen de 1,000 consultas mensuales y 10 documentos procesados.

---

## 🧮 Metodología de Cálculo

Los costos se calculan con base en:

- **Volumen estimado:** 1,000 consultas de usuario/mes + 10 documentos procesados/mes.
- **Precios públicos** al momento del análisis (Junio 2026).
- **Uso típico** de los servicios (sin considerar niveles gratuitos).
- **Tráfico entre nubes:** Se contabiliza el egress de GCP hacia Azure (consultas) y de AWS hacia GCP (ingesta).

---

## ☁️ Desglose por Proveedor

### 1. Microsoft Azure

| Servicio | Detalle | Costo mensual estimado |
|----------|---------|-------------------------|
| **Azure OpenAI (GPT-4o)** | 1,000 consultas × 500 tokens promedio = 500,000 tokens de entrada + 150,000 tokens de salida (ratio 3:1). Precio: $5.00 / 1M input, $15.00 / 1M output. | $5.00 × 0.5 + $15.00 × 0.15 = **$4.75** |
| **Azure OpenAI (Embeddings)** | 1,000 consultas × 1 embedding = 1,000 llamadas. Precio: $0.0001 / 1k tokens (promedio 100 tokens/consulta) → 100k tokens/mes → **$0.01** | **$0.01** |
| **Azure Functions (Consumption Plan)** | 1,000 ejecuciones × 200 MB‑s (memoria) + 500 ms promedio. Primer 1M ejecuciones gratis; luego $0.20 / 1M. Costo ≈ $0.20 (insignificante). | **$0.20** |
| **Azure Static Web Apps** | Plan gratuito (hobby) para hasta 100 GB de ancho de banda. | **$0.00** |
| **Azure Storage (para Functions)** | Almacenamiento de logs y estado (≈ 1 GB). $0.02/GB. | **$0.02** |
| **Subtotal Azure** | | **~$5.00** |

### 2. AWS (Ingesta y Almacenamiento)

| Servicio | Detalle | Costo mensual estimado |
|----------|---------|-------------------------|
| **AWS Lambda** | 10 ejecuciones/mes (una por documento). Duración: 60 segundos, 512 MB. Precio: $0.00001667 / GB‑s. Cálculo: 10 × 512 MB × 60s = 307,200 GB‑s → $5.12 | **$5.12** |
| **AWS S3 (Almacenamiento)** | 10 archivos × 5 MB promedio = 50 MB. Primer 50 GB gratis (12 meses); después $0.023/GB. Costo insignificante. | **$0.00** |
| **AWS S3 (Transferencia saliente)** | Ingesta: S3 → Lambda (dentro de AWS) sin costo. Egress hacia GCP (chunking) ≈ 5 MB × 10 = 50 MB. Primer 100 GB gratis (12 meses); después $0.09/GB. | **$0.00** |
| **Subtotal AWS** | | **~$5.12** |

### 3. Google Cloud Platform (GCP)

| Servicio | Detalle | Costo mensual estimado |
|----------|---------|-------------------------|
| **Cloud Run (Retrieval Service)** | 1,000 consultas × 0.5 GB‑s (memoria) × 0.2s (promedio) = 100 GB‑s. Precio: $0.000024 / GB‑s → $0.0024. Con mínimo de 1 instancia (cold start) adicional: 24h × 30 = 720h × 0.5 GB = 360 GB‑h × $0.000024 = $0.0086. | **$0.01** |
| **Cloud Run (Chunking Service)** | 10 ejecuciones × 2 GB‑s (memoria) × 30s = 600 GB‑s. Precio: $0.000024 / GB‑s → $0.0144. | **$0.02** |
| **AlloyDB (pgvector)** | Instancia primaria: 2 vCPU, 8 GB RAM (aprox. $0.50/hora) = $0.50 × 720h = **$360.00**. | **$360.00** |
| **AlloyDB (Storage)** | 100 GB SSD persistentes (incluye backups). $0.17/GB/mes = **$17.00**. | **$17.00** |
| **Network Egress (GCP → Azure)** | 1,000 consultas × 50 KB (chunks) ≈ 50 MB. Primer 1 GB gratis (por mes); después $0.12/GB. | **$0.00** |
| **Subtotal GCP** | | **~$377.03** |

### 💰 Costo Total Mensual Estimado

| Proveedor | Costo |
|-----------|-------|
| Azure | $5.00 |
| AWS | $5.12 |
| GCP | $377.03 |
| **Total** | **~$387.15** |

> **Observación:** El costo está dominado por AlloyDB (~$377/mes). Sin optimización, este es el principal cuello de botella financiero.

---

## 📊 Costo por Consulta y por 1k Tokens

| Métrica | Valor |
|---------|-------|
| **Costo por consulta** | $387.15 / 1,000 = **$0.39** |
| **Costo por 1k tokens de entrada** | $0.39 / (500 tokens entrada + 150 tokens salida) × 1000 ≈ **$0.60** |

---

## 🚀 Estrategias de Optimización (FinOps)

### 1. Reducción del costo de AlloyDB

| Estrategia | Ahorro estimado | Implementación |
|------------|-----------------|----------------|
| **Escalar a instancia más pequeña** (1 vCPU, 4 GB RAM) → $0.25/hora | $180/mes | Cambiar tipo de máquina en AlloyDB. |
| **Uso de instancia de desarrollo** (stop/start) si no hay tráfico 24/7 | $180/mes | Automatizar apagado durante la noche (ej. 8h/día). |
| **Caching de embeddings** (Redis/Memcached) para consultas frecuentes | Reducción de CPU/RAM | Implementar caché de resultados de retrieval. |
| **Migrar a pgvector en Cloud SQL** (más económico) | $150/mes | Cloud SQL PostgreSQL con pgvector es más barato que AlloyDB. |

**Recomendación:** Migrar a **Cloud SQL (PostgreSQL + pgvector)** con 1 vCPU, 4 GB RAM (≈ $0.15/hora) reduciría el costo a ~$108/mes, un ahorro de **$252/mes**.

---

### 2. Minimización de Egress entre Nubes

| Estrategia | Ahorro estimado | Implementación |
|------------|-----------------|----------------|
| **Compresión de chunks** (gzip) antes de enviar desde GCP a Azure | 70% menos ancho de banda | Agregar `Content-Encoding: gzip` en las respuestas de Cloud Run. |
| **Caching en Azure** de respuestas frecuentes | Reducción de llamadas a GCP | Usar Azure Redis Cache o almacenamiento en memoria. |
| **Batch embeddings** (en lugar de uno por consulta) | Menos llamadas a Azure OpenAI | Agrupar varias consultas en una sola solicitud de embeddings (si es posible). |

---

### 3. Optimización de Azure OpenAI

| Estrategia | Ahorro estimado | Implementación |
|------------|-----------------|----------------|
| **Usar GPT‑4o Mini** en lugar de GPT‑4o (cuando sea viable) | 70% menor costo por token | Implementar routing de modelos según complejidad de la pregunta. |
| **Reducir `max_tokens`** a 300 en lugar de 500 | 40% menos tokens de salida | Ajustar parámetro en `get_chat_completion`. |
| **Cachear respuestas** para preguntas frecuentes | Hasta 80% menos llamadas | Usar Redis o Azure Cache para almacenar respuestas comunes. |

---

### 4. Optimización de AWS Lambda

| Estrategia | Ahorro estimado | Implementación |
|------------|-----------------|----------------|
| **Reducir memoria de Lambda** a 256 MB (si es suficiente) | 50% menor costo | Cambiar `--memory-size` en el script de despliegue. |
| **Procesar documentos en lotes** (varios PDFs en una ejecución) | Menos invocaciones | Modificar Lambda para procesar múltiples archivos. |

---

## 📈 Comparativa: Antes vs. Después de Optimizaciones

| Concepto | Sin optimizar | Con optimizaciones | Ahorro |
|----------|---------------|--------------------|--------|
| **AlloyDB** | $377.03 | $108.00 (Cloud SQL) | $269.03 |
| **Azure OpenAI** | $4.76 | $1.50 (GPT-4o Mini + caching) | $3.26 |
| **AWS Lambda** | $5.12 | $2.00 (menor memoria + batching) | $3.12 |
| **Cloud Run** | $0.03 | $0.03 | $0.00 |
| **Otros** | $0.22 | $0.22 | $0.00 |
| **Total mensual** | **$387.15** | **~$111.75** | **$275.40 (71%)** |

---

## 📌 Recomendaciones FinOps Finales

1. **Migrar AlloyDB a Cloud SQL** con pgvector (ahorro inmediato).
2. **Implementar caching** de respuestas y embeddings para reducir llamadas a Azure OpenAI y GCP.
3. **Ajustar tamaños de instancias** y escalar a cero durante horas de baja demanda.
4. **Monitorizar costos** con herramientas nativas (Azure Cost Management, AWS Cost Explorer, GCP Billing).
5. **Establecer alertas** de presupuesto para evitar desviaciones.

---

## 🧠 Lecciones Aprendidas

- El costo de la base de datos vectorial puede dominar el presupuesto en arquitecturas multi‑cloud.
- El tráfico entre nubes (egress) tiene un impacto menor que el costo de la infraestructura persistente.
- Las optimizaciones deben enfocarse primero en los servicios con mayor gasto (en este caso, AlloyDB).
- El uso de caching y modelos más económicos (GPT-4o Mini) son estrategias de alto impacto.

---

## 📚 Documentación Relacionada

- [Guía de Administrador](guia-administrador.md) – Configuración de instancias y escalado.
- [Arquitectura Multicloud](arquitectura.mermaid) – Diagrama de red y flujo de datos.
- [README Principal](../README.md) – Visión general del proyecto.

---

**Autor:** David Yurvilca  
**Fecha:** Junio 2026  
**Versión:** 1.0