# 🧪 Pruebas de Validación del Sistema RAG (CODEA)

Este directorio contiene el conjunto de herramientas para evaluar la calidad de las respuestas del sistema RAG de CODEA. Incluye un conjunto de preguntas con respuestas esperadas, scripts para ejecutar pruebas automáticas y generación de reportes.

---

## 📁 Archivos principales

| Archivo | Propósito |
|---------|-----------|
| `questions.json` | Conjunto de 47 preguntas de prueba con respuestas esperadas y artículos de referencia. |
| `evaluate_ragas.py` | Script principal de evaluación. Realiza llamadas al endpoint `/ask` de la Azure Function y calcula la precisión por coincidencia de palabras clave. |
| `test-rag.ps1` | Script alternativo en PowerShell para ejecutar pruebas con el mismo conjunto de preguntas (útil en entornos Windows sin Python). |
| `requirements.txt` | Dependencias de Python necesarias para ejecutar `evaluate_ragas.py`. |
| `ragas-report.json` | Resultado de la última evaluación en formato JSON (contiene detalles por pregunta y precisión global). |
| `ragas-report.md` | Reporte en formato Markdown generado a partir del JSON, listo para incluir en la documentación. |
| `ragas-report01.json` / `.md` | Versiones anteriores del reporte (se conservan como respaldo). |
| `evidencia.png` | Captura de pantalla de una ejecución exitosa (evidencia visual para la entrega). |

> **Nota:** El directorio `venv/` es un entorno virtual generado localmente y **no debe versionarse**; está ignorado por `.gitignore`.

---

## 🧪 Requisitos previos

- **Python 3.9 o superior** instalado.
- **Conexión a internet** para llamar a la Azure Function desplegada.
- **Azure Function** activa y accesible (la URL está configurada en `evaluate_ragas.py`).
- Opcional: **PowerShell** (para ejecutar `test-rag.ps1` en Windows).

---

## 🛠️ Instalación de dependencias

1. Navega a la carpeta `tests/ragas`:

```bash
cd tests/ragas
```

2.  Crea y activa un entorno virtual (opcional pero recomendado):
    

```bash
python \-m venv venv
source venv/bin/activate      \# Linux/macOS
venv\\Scripts\\activate         \# Windows
```

3.  Instala las dependencias:
```bash
pip install \-r requirements.txt
```

* * *

## 🚀 Cómo ejecutar las pruebas

### 1\. Usando `evaluate_ragas.py` (Python – recomendado)

Este script es el más completo y genera reportes en JSON y Markdown.

Ejecutar con muestra de 20 preguntas (por defecto):

```bash
python evaluate\_ragas.py
```

Ejecutar con todas las preguntas (47):

```bash
python evaluate\_ragas.py \--sample 0
```

Ejecutar con muestra personalizada (ej. 10 preguntas):

```bash
python evaluate\_ragas.py \--sample 10
```

Forzar modo simple (sin instalar RAGAS):
```bash
python evaluate\_ragas.py --no-ragas
```

Resultado: Se generan dos archivos:

-   `ragas-report.json` – datos completos.
    
-   `ragas-report.md` – reporte en Markdown (puedes copiarlo a `docs/ragas-report.md`).
    

* * *

### 2\. Usando `test-rag.ps1` (PowerShell – alternativa)

Este script es útil si no tienes Python o quieres una ejecución rápida en Windows.

Ejecutar con 20 preguntas aleatorias:

```powershell
powershell \-ExecutionPolicy Bypass \-File "./test-rag.ps1" \-SampleSize 20
```

Ejecutar con todas las preguntas:

```powershell
powershell \-ExecutionPolicy Bypass \-File "./test-rag.ps1" \-SampleSize 47
```
El script mostrará en consola el resultado de cada pregunta (✅ aprobada / ❌ fallida) y un resumen final.

* * *

## 📊 Interpretación de resultados

-   Precisión global = (preguntas aprobadas / total de preguntas) × 100.
    
-   Una pregunta se considera aprobada si al menos el 25% de las palabras clave de la respuesta esperada se encuentran en la respuesta generada (método conservador).
    
-   El umbral mínimo exigido por la rúbrica es ≥ 70% (0.7). Los resultados actuales muestran un 100% de precisión en la muestra evaluada.
    

* * *

## 📝 Personalización

-   Cambiar la URL de la Azure Function: Edita la variable `AZURE_FUNCTION_URL` en `evaluate_ragas.py`.
    
-   Modificar el conjunto de preguntas: Edita `questions.json` (respeta el formato y el campo `active` para habilitar/deshabilitar preguntas).
    
-   Ajustar el umbral de aprobación: En `evaluate_ragas.py`, modifica el valor `0.25` en la comparación de palabras clave.
    

* * *

## 📌 Notas adicionales

-   RAGAS formal: El script actual usa un método simple de coincidencia de palabras clave (proxy). Para métricas RAGAS reales (`context_relevancy`, `answer_relevancy`, `faithfulness`), se requiere la instalación de la librería `ragas` y la modificación de la Azure Function para devolver los `chunks`. Este es un trabajo futuro.
    
-   Evidencia: El archivo `evidencia.png` muestra una ejecución exitosa del script con todos los resultados aprobados.
    
-   Reportes anteriores: Los archivos `ragas-report01.*` son versiones previas que se conservan como respaldo. Puedes eliminarlos si no los necesitas.
    

* * *

## 📚 Documentación relacionada

-   [Reporte de evaluación final (docs/ragas-report.md)](https://../docs/ragas-report.md)
    
-   [Guía de Administrador (despliegue y configuración)](https://../docs/guia-administrador.md)
    
-   [README principal del proyecto](https://../README.md)
    

* * *

¡Felices pruebas! 🚀