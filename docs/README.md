# 📚 Documentación del Proyecto CODEA RAG

Bienvenido a la documentación completa del proyecto **CODEA RAG**, una plataforma serverless multi‑cloud para consultas sobre pensión de alimentos en Perú.

Este directorio contiene toda la documentación técnica y funcional del proyecto, organizada por temática y nivel de detalle.

---

## 📋 Índice de Documentos

| Documento | Descripción | Estado |
|-----------|-------------|--------|
| [Guía de Usuario](guia-usuario.md) | Instrucciones para el usuario final sobre cómo usar la aplicación, ejemplos de preguntas e interpretación de respuestas. | ✅ Completado |
| [Guía de Administrador](guia-administrador.md) | Guía técnica para el despliegue, configuración, monitoreo y solución de problemas del sistema. | ✅ Completado |
| [Patrón de Diseño LLM](patron-diseno-llm.md) | Descripción y justificación del patrón de diseño LLM implementado (Self-Query Retriever), con diagramas y trade-offs. | ✅ Completado |
| [Contenerización (Docker)](contenizacion.md) | Detalle de los Dockerfiles, buenas prácticas de contenerización, seguridad (Trivy) y justificación de su uso. | ✅ Completado |
| [CI/CD Multinube](ci-cd.md) | Estrategia de Integración Continua y Despliegue Continuo, scripts existentes, propuesta de GitHub Actions y Terraform. | ✅ Completado |
| [Optimización de Costos (FinOps)](costos.md) | Análisis detallado de costos mensuales por proveedor, costo por consulta y estrategias de optimización (FinOps). | ✅ Completado |
| [Observabilidad Cross-Cloud](observabilidad.md) | Herramientas de monitoreo (App Insights, CloudWatch, Cloud Logging), métricas clave, alertas y trazabilidad del flujo. | ✅ Completado |
| [Reporte de Evaluación](ragas-report.md) | Resultados de la evaluación del sistema RAG (100% de precisión en validación por palabras clave), análisis y conclusiones. | ✅ Completado |
| [Diagrama de Arquitectura](arquitectura.mermaid) | Diagrama Mermaid de la arquitectura multi‑cloud del sistema (Azure, AWS, GCP). | ✅ Completado |
| [Arquitectura de Sistemas](arquitectura.md)  | Explicación detallada de la arquitectura multi-cloud, componentes, flujos, red y seguridad. Incluye el diagrama Mermaid.| ✅ Completado |
| [Entrega Final](ENTREGA_FINAL.md)  | Documento integrador de 20-25 páginas con todos los entregables del proyecto.| ✅ Completado |

---

## 🗺️ Mapa de Lectura por Rol

| Rol | Documentos recomendados |
|-----|-------------------------|
| **Usuario final** | [Guía de Usuario](guia-usuario.md) |
| **Administrador / DevOps** | [Guía de Administrador](guia-administrador.md), [CI/CD](ci-cd.md), [Observabilidad](observabilidad.md) |
| **Arquitecto de Soluciones** | [Patrón de Diseño LLM](patron-diseno-llm.md), [Arquitectura](arquitectura.mermaid), [Costos](costos.md) |
| **Desarrollador** | [Contenerización](contenizacion.md), [CI/CD](ci-cd.md), [Guía de Administrador](guia-administrador.md) |
| **Evaluador / Profesor** | [Reporte RAGAS](ragas-report.md), [Patrón de Diseño LLM](patron-diseno-llm.md), [Costos](costos.md) |

---

## 📂 Estructura del Proyecto

El repositorio completo tiene la siguiente estructura:
```text
codea-rag/
├── docs/ # 📚 Esta carpeta (documentación)
│ ├── README.md # ← Estás aquí
│ ├── guia-usuario.md
│ ├── guia-administrador.md
│ ├── patron-diseno-llm.md
│ ├── contenerizacion.md
│ ├── ci-cd.md
│ ├── costos.md
│ ├── observabilidad.md
│ ├── ragas-report.md
│ └── arquitectura.mermaid
├── frontend/ # Código del frontend (React)
├── azure-function/ # Orquestador (Azure Functions)
├── aws-lambda-ingesta/ # Ingesta (AWS Lambda)
├── gcp-services/ # Servicios en GCP (Chunking y Retrieval)
│ ├── chunking-service/
│ └── retrieval-service/
├── documentos-normas/ # PDFs fuente (normas legales)
├── sql/ # Scripts de base de datos
├── tests/ # Pruebas (incluye RAGAS)
└── README.md # README principal del proyecto
```

---

## 🔗 Enlaces Externos

| Recurso | Enlace |
|---------|--------|
| **Frontend desplegado** | [https://victorious-tree-02708ac0f.7.azurestaticapps.net/](https://victorious-tree-02708ac0f.7.azurestaticapps.net/) |
| **Video de presentación** | [Enlace a Google Slides](https://docs.google.com/presentation/d/1pbYLm9DBwf0ocX7UEz78iUbAbPO1VoSt/edit?usp=drive_link&ouid=108325222194450107540&rtpof=true&sd=true) |
| **Repositorio GitHub** | [https://github.com/systemyuri/codea-rag-multinube](https://github.com/systemyuri/codea-rag-multinube) |

---

## 📌 Notas sobre la Documentación

- Todos los documentos están escritos en **Markdown** y pueden visualizarse directamente en GitHub o en cualquier editor compatible.
- Los diagramas están en **Mermaid** y se renderizan automáticamente en GitHub.
- Los documentos están actualizados a **Junio 2026** y reflejan el estado final del proyecto.
- Para cualquier duda o sugerencia, abre un **Issue** en el repositorio o contacta al autor.

---

## 👤 Autor

**David Yurvilca**  
*Estudiante del Programa de AI/LLM Solution Architect*  
*Curso: Diseño de Infraestructura Escalable*  
*BSG Institute*

---

**¡Gracias por visitar la documentación de CODEA RAG!** 🚀