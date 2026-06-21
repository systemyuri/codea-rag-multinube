# 🧠 Patrón de Diseño LLM – CODEA RAG

## 📌 Resumen

Este documento describe el patrón de diseño LLM implementado en CODEA RAG, justifica su selección, detalla los trade-offs y muestra su integración en el pipeline RAG distribuido.

---

## 🎯 Patrón Seleccionado

**Patrón principal:** *RAG Básico + Self-Query Retriever*  
**Patrón secundario:** *Guardrail de Ingesta* (control de duplicados y validación de documentos)

### Descripción

- **RAG Básico:** El sistema recupera fragmentos (chunks) de la base de datos vectorial mediante similitud coseno, los combina en un prompt y los envía al LLM para generar una respuesta.
- **Self-Query Retriever:** Antes de la búsqueda, se extraen filtros estructurados (ej. `norm_code`, `title`) de la pregunta del usuario usando **expresiones regulares**, y se aplican como condiciones `WHERE` en la consulta SQL. Esto reduce el espacio de búsqueda y mejora la precisión.
- **Guardrail de Ingesta:** Durante la subida de documentos, se verifica el hash del archivo para evitar duplicados, y se registran metadatos (norm_code, title, filename) que luego son usados por el Self-Query Retriever.

---

## 🧩 Justificación Técnica

| Criterio | Evaluación |
|----------|------------|
| **Latencia** | El Self-Query Retriever añade un paso de extracción de filtros (regex, < 5ms) y una cláusula `WHERE` en la consulta SQL. No se usa un modelo adicional, por lo que el impacto en latencia es mínimo (~+10% en tiempo de retrieval). |
| **Costo** | No se invoca un LLM para extraer filtros, por lo que el costo adicional es nulo. El guardrail de ingesta solo implica una consulta SQL adicional, también de costo insignificante. |
| **Calidad** | El filtrado por metadatos elimina chunks irrelevantes, mejorando la precisión de la recuperación. Esto se refleja en una puntuación RAGAS de **0.77**, superior al mínimo exigido (0.7). |
| **Seguridad** | El guardrail de ingesta previene la subida de documentos corruptos o duplicados, y el control de metadatos evita que se procesen documentos no autorizados. |
| **Complejidad** | La implementación es simple: regex para extracción y filtros SQL. No requiere infraestructura adicional ni dependencias externas. |

---

## 📊 Diagrama del Patrón en el Pipeline

El siguiente diagrama muestra el flujo completo, destacando el paso de **Self-Query** y el **Guardrail de Ingesta**:

```mermaid
sequenceDiagram
    participant User as Usuario
    participant Frontend as Frontend (Azure)
    participant Orchestrator as Orquestador (Azure Functions)
    participant Retrieval as Retrieval Service (GCP Cloud Run)
    participant VectorDB as AlloyDB (pgvector)
    participant LLM as Azure OpenAI

    User->>Frontend: Pregunta en lenguaje natural
    Frontend->>Orchestrator: POST /ask {question}

    Note over Orchestrator: Self-Query Retriever
    Orchestrator->>Orchestrator: extraer_filtros(question)
    Orchestrator->>Orchestrator: generate_embedding(question)

    Orchestrator->>Retrieval: POST /retrieve {vector, filtros}
    Retrieval->>VectorDB: SELECT ... WHERE norm_code ILIKE '%LEY 27337%'
    VectorDB-->>Retrieval: Chunks filtrados
    Retrieval-->>Orchestrator: {chunks}

    Orchestrator->>Orchestrator: build_prompt(question, chunks)
    Orchestrator->>LLM: chat_completion(prompt)
    LLM-->>Orchestrator: Respuesta generada

    Orchestrator-->>Frontend: {answer}
    Frontend-->>User: Respuesta con citas
 ```   

 ## Detalle del Guardrail de Ingesta

```mermaid
sequenceDiagram
    participant Admin as Administrador
    participant S3 as AWS S3
    participant Lambda as AWS Lambda
    participant Chunking as Chunking Service (GCP)
    participant DB as AlloyDB

    Admin->>S3: Sube PDF (con título y norm_code)
    S3->>Lambda: Evento de subida
    Lambda->>Lambda: Verifica duplicado por hash
    Lambda->>Chunking: Envía PDF para procesar
    Chunking->>Chunking: Extrae texto y fragmenta
    Chunking->>DB: Guarda chunks y metadatos
    DB-->>Chunking: Confirmación
    Chunking-->>Lambda: OK
    Lambda-->>S3: Actualiza metadatos
```

## ⚖️ Trade-offs y Alternativas Consideradas

| Alternativa | Ventajas | Desventajas | ¿Por qué no se eligió? |
| --- | --- | --- | --- |
| **RAG + Reranking** | Mayor precisión en la recuperación | Añade latencia y costo por el modelo de reranking | El costo adicional no se justifica con solo 538 chunks; la precisión actual (0.77) es suficiente |
| **Model Routing** | Optimiza costo/rendimiento | Complejidad de clasificación y mantenimiento | El caso de uso es homogéneo (pensión de alimentos); no se necesitan diferentes modelos |
| **Mixture of Agents** | Alta calidad y reducción de alucinaciones | Costo muy alto, latencia alta | No es viable en un entorno serverless con recursos limitados |
| **Self-Query (elegido)** | Precisión mejorada, costo nulo, simple | Requiere metadatos estructurados y extracción precisa de filtros | Se eligió porque aprovecha los metadatos ya existentes (norm\_code, title) y la extracción con regex es suficiente para el dominio |
| **Hybrid RAG (Vector + KG)** | Captura relaciones complejas | Muy complejo de implementar y mantener | El dominio legal no requiere relaciones jerárquicas complejas; el vector search es suficiente |

* * *

## 🔍 Impacto en el Sistema

| Dimensión | Impacto |
| --- | --- |
| **Latencia total** | Aumento de ~200 ms debido al filtrado SQL, pero reduce el tiempo de búsqueda al limitar el número de chunks a comparar. |
| **Costo por consulta** | Sin aumento significativo (solo una consulta SQL adicional y procesamiento de regex). |
| **Calidad de respuesta** | Mejora porque se evitan chunks de documentos no relacionados. |
| **Seguridad** | El guardrail de ingesta evita la contaminación de la base de conocimiento con documentos duplicados o mal formados. |
| **Mantenibilidad** | La lógica de extracción está centralizada en `extraer_filtros()`, fácil de actualizar si cambia el formato de las preguntas. |

* * *

## 📝 Código de Referencia

### Extracción de filtros (Azure Function)

```python
def extraer_filtros(pregunta: str) -> dict:
    filtros = {}
    match = re.search(
        r"(?i)\b(ley|decreto legislativo|decreto supremo|resolucion administrativa|constitucion politica)\s*([0-9-]+)",
        pregunta,
    )
    if match:
        tipo = match.group(1).strip().upper()
        numero = match.group(2).strip()
        if tipo == "LEY":
            filtros["norm_code"] = f"LEY {numero}"
        # ... otros tipos
    return filtros
```

### Aplicación de filtros (Retrieval Service)
```python
def build_filter_conditions(filtros):
    conditions = []
    params = []
    if "norm_code" in filtros:
        conditions.append("dm.norm_code ILIKE %s")
        params.append(f"%{filtros['norm_code']}%")
    # ... otros filtros
    return where_clause, params
```

### Consulta SQL final
```sql
SELECT c.content, c.source, c.article, dm.title AS document_title
FROM chunks c
INNER JOIN documentos_metadata dm ON c.document_id = dm.id
WHERE 1=1 AND dm.norm_code ILIKE '%LEY 27337%'
ORDER BY c.embedding <=> %s::vector
LIMIT 20;
```

## 📚 Documentos Relacionados

-   [Guía de Administrador](https://guia-administrador.md/) – Despliegue y configuración del Self-Query Retriever.
    
-   [Pipeline RAG Distribuido](https://pipeline-rag.md/) – Detalle técnico del flujo RAG.
    
-   [Reporte RAGAS](https://ragas-report.md/) – Resultados de evaluación con el patrón implementado.
    

* * *

**Autor:** David Yurvilca  
**Fecha:** Junio 2026  
**Versión:** 1.0