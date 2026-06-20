# 📄 Documentos Normativos – Fuentes para CODEA RAG

Esta carpeta contiene los archivos PDF de las normas legales peruanas utilizadas como fuente de conocimiento para el sistema RAG.  
Los documentos se organizan en subcarpetas según el **área del derecho** a la que pertenecen, y cada archivo sigue un formato de nombre estandarizado para facilitar su identificación y procesamiento.

---

## 📂 Estructura de Carpetas

La carpeta principal `documentos-normas/` contiene las siguientes subcarpetas:

| Carpeta | Contenido |
|---------|-----------|
| `administrativa/` | Normas de derecho administrativo (resoluciones, decretos, directivas, etc.) |
| `constitución/` | Texto de la Constitución Política del Perú y sus modificaciones. |
| `leyes/` | Leyes ordinarias, decretos legislativos, decretos de urgencia, etc. |
| `penal/` | Normas de derecho penal y procesal penal (Código Penal, etc.). |

Cada subcarpeta puede contener varios archivos PDF.

---

## 📝 Formato de Nombre de Archivos

Cada archivo PDF debe seguir el siguiente formato:
```text
[número o código de la norma]#[Título descriptivo].pdf
```

- **Antes del `#`**: Identificador único de la norma (ej. número de ley, artículo, código).
- **Después del `#`**: Título o descripción breve del contenido (puede ir en mayúsculas o minúsculas, según prefieras).

### Ejemplos

| Nombre de archivo | Significado |
|-------------------|-------------|
| `ley 26872#CONCILIACION.pdf` | Ley N° 26872 sobre conciliación. |
| `decreto 123#PROCEDIMIENTO ADMINISTRATIVO.pdf` | Decreto que regula procedimientos administrativos. |
| `art 42#CODIGO PENAL.pdf` | Artículo 42 del Código Penal. |

> **Nota:** El sistema de ingesta (Chunking Service) extrae el texto del PDF y utiliza el nombre del archivo para etiquetar los fragmentos, por lo que es importante que sea descriptivo.

---

## 🔄 Proceso de Ingesta

1. Un administrador coloca (o sube) un nuevo PDF en la subcarpeta correspondiente dentro del repositorio local, o lo sube directamente al bucket S3 (`codea-docs-ingesta`).
2. AWS Lambda detecta la subida al bucket y envía el archivo al **Chunking Service** en GCP.
3. El servicio extrae el texto, lo fragmenta en chunks, genera embeddings con Azure OpenAI y los almacena en AlloyDB (pgvector).
4. Los PDFs originales se conservan en S3 y en el repositorio para referencia y posible re-procesamiento.

---

## 📌 Buenas Prácticas

- **Formato:** Solo PDFs con texto digital (no imágenes escaneadas sin OCR).
- **Tamaño:** Idealmente < 20 MB por archivo.
- **Actualización:** Si una norma cambia, sube la nueva versión con un sufijo de versión (ej. `ley-26872-v2#CONCILIACION-ACTUALIZADA.pdf`) y notifica al administrador para que elimine la anterior del sistema.
- **Organización:** Coloca cada PDF en la carpeta temática que mejor corresponda. Si una norma abarca varias áreas, elige la más relevante o crea una copia (evita duplicados innecesarios).

---

## 📖 Documentación Relacionada

- [Guía de Administrador](../docs/guia-administrador.md) – Procedimientos de ingesta y gestión.
- [README del Chunking Service](../gcp-services/chunking-service/README.md) – Detalles técnicos del procesamiento.
- [README del AWS Lambda de ingesta](../aws-lambda-ingesta/README.md) – Configuración del trigger de S3.

---

**¡Mantén esta carpeta organizada para garantizar la calidad del sistema RAG!** 🚀