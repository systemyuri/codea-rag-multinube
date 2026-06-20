# 🧠 CODEA – RAG Serverless Multi-Cloud para Consulta de Pensión de Alimentos en Perú

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Azure](https://img.shields.io/badge/Azure-Functions%20%7C%20Static%20Web%20Apps-0078D4)](https://azure.microsoft.com)
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Lambda-FF9900)](https://aws.amazon.com)
[![GCP](https://img.shields.io/badge/GCP-AlloyDB%20%7C%20Cloud%20Run-4285F4)](https://cloud.google.com)

**CODEA** es un asistente legal ciudadano que responde preguntas sobre **pensión de alimentos en Perú**, utilizando un sistema RAG (Retrieval-Augmented Generation) distribuido en tres nubes: **GCP** (base de datos vectorial y microservicios), **AWS** (ingesta de documentos) y **Azure** (orquestador, frontend y LLM).

> 🎯 **Objetivo del proyecto**: Proporcionar una plataforma serverless, escalable y multi-cloud que permita a los ciudadanos obtener respuestas basadas en normas legales oficiales (leyes, decretos, códigos, resoluciones) de forma rápida y confiable.

---

## 📋 Tabla de contenido

- [Arquitectura general](#-arquitectura-general)
- [Tecnologías utilizadas](#-tecnologías-utilizadas)
- [Requisitos previos](#-requisitos-previos)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Despliegue paso a paso](#-despliegue-paso-a-paso)
  - [1. GCP – Base de datos vectorial y microservicios](#1-gcp--base-de-datos-vectorial-y-microservicios)
  - [2. AWS – Ingesta de documentos](#2-aws--ingesta-de-documentos)
  - [3. Azure – Orquestador y frontend](#3-azure--orquestador-y-frontend)
- [Frontend – Uso y personalización](#-frontend--uso-y-personalización)
- [Evaluación y métricas](#-evaluación-y-métricas)
- [Monitoreo y observabilidad](#-monitoreo-y-observabilidad)
- [Costos y optimización FinOps](#-costos-y-optimización-finops)
- [CI/CD con GitHub Actions](#-cicd-con-github-actions)
- [Contribuciones y soporte](#-contribuciones-y-soporte)
- [Licencia](#-licencia)

---

## 🏗️ Arquitectura general

![Arquitectura CODEA](docs/arquitectura.mermaid)

```mermaid
flowchart TD
    subgraph "Azure Cloud"
        A[React Frontend<br/>Azure Static Web Apps]
        B[Azure Functions<br/>Orquestador]
        C[Azure OpenAI<br/>Embeddings + Chat]
        D[Application Insights]
    end

    subgraph "AWS Cloud"
        E[S3 Bucket<br/>Documentos PDF]
        F[AWS Lambda<br/>Ingesta]
        G[API Gateway<br/>Opcional]
    end

    subgraph "GCP Cloud"
        H[AlloyDB pgvector<br/>Vector Store]
        I[Cloud Run<br/>Chunking Service]
        J[Cloud Run<br/>Retrieval Service]
        K[Cloud Logging]
    end

    A -->|POST /ask| B
    B -->|embedding| C
    B -->|vector query| J
    J -->|similarity search| H
    H -->|chunks| J
    J -->|chunks| B
    B -->|prompt + chunks| C
    C -->|answer| B
    B -->|answer| A

    E -->|upload event| F
    F -->|download PDF| E
    F -->|texto extraído| I
    I -->|chunks| F
    F -->|embedding| C
    F -->|store vectors| H

    D -.->|logs/metrics| B
    K -.->|logs| I
    K -.->|logs| J