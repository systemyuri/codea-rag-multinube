#!/usr/bin/env python3
"""
Script de prueba para el endpoint /ask de la Azure Function de CODEA RAG.
Uso: python test_azure_ask.py
"""

import requests
import json
import sys
import time

# ============================================================
# CONFIGURACIÓN - ACTUALIZA ESTOS VALORES
# ============================================================

# URL completa del endpoint /ask con su código de autenticación
AZURE_FUNCTION_URL = "https://codea-orchestrator.azurewebsites.net/api/ask?code=APgUNXw0hbrLWtTjXHnXUU6JwAXKjZbeMMa9enOmNYW9AzFup1vvTA=="

# Pregunta de prueba (cámbiala por la que quieras)
TEST_QUESTION = "¿Qué dice la Ley 27337 sobre pensiones de alimentos?"

# Timeout en segundos (aumenta si es necesario)
TIMEOUT_SECONDS = 60

# ============================================================
# FIN DE LA CONFIGURACIÓN
# ============================================================


def test_azure_ask(question: str) -> dict:
    """
    Envía una pregunta al endpoint /ask de la Azure Function.
    Retorna la respuesta completa del servidor o el error.
    """
    # Preparar el payload
    payload = {"question": question}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"\n🚀 Enviando pregunta a la Azure Function...")
    print(f"📝 Pregunta: {question}")
    print(f"🔗 URL: {AZURE_FUNCTION_URL}")
    print(f"⏱️  Timeout: {TIMEOUT_SECONDS} segundos")
    print("-" * 60)

    start_time = time.time()

    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )

        elapsed = time.time() - start_time
        print(f"⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")

        # Mostrar información del status
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")

        # Intentar parsear la respuesta como JSON
        try:
            response_data = response.json()
            print("\n📦 Respuesta JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            # Si no es JSON, mostrar el texto plano
            print("\n📄 Respuesta (texto plano):")
            print(response.text[:1000])  # Mostrar solo los primeros 1000 caracteres

        # Verificar si fue exitoso
        if response.status_code == 200:
            print("\n✅ ¡La Azure Function respondió correctamente!")
        else:
            print(f"\n⚠️  La Azure Function respondió con error {response.status_code}")

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "data": response_data if 'response_data' in locals() else None,
            "raw_text": response.text
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR: Timeout después de {elapsed:.2f} segundos")
        print(f"   La Azure Function no respondió en {TIMEOUT_SECONDS} segundos.")
        print("   Posibles causas:")
        print("   - El retrieval service (Cloud Run) está tardando demasiado o no responde.")
        print("   - La conexión a la base de datos (AlloyDB) está fallando.")
        print("   - La Azure Function está sobrecargada o tiene un error interno.")
        return {"success": False, "error": "timeout", "elapsed": elapsed}

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR de conexión: {e}")
        print("   No se pudo conectar a la Azure Function.")
        print("   Verifica que la URL sea correcta y que el servicio esté activo.")
        return {"success": False, "error": "connection_error", "details": str(e)}

    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
        return {"success": False, "error": "unexpected_error", "details": str(e)}


def main():
    """Función principal del script."""
    print("=" * 60)
    print("🧪 TEST DEL ENDPOINT /ask DE LA AZURE FUNCTION")
    print("=" * 60)

    # Si se pasa una pregunta como argumento, usarla
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = TEST_QUESTION

    result = test_azure_ask(question)

    print("\n" + "=" * 60)
    if result.get("success"):
        print("✅ PRUEBA EXITOSA")
        if result.get("data") and "answer" in result["data"]:
            print("\n📝 Respuesta del asistente:")
            print(result["data"]["answer"])
    else:
        print("❌ PRUEBA FALLIDA")
        if result.get("error") == "timeout":
            print("\n🔍 SUGERENCIAS PARA EL TIMEOUT:")
            print("   1. Verifica los logs de Cloud Run para ver si el retrieval service está")
            print("      recibiendo la solicitud y cuánto tarda en procesarla.")
            print("   2. Aumenta el timeout en la Azure Function (en el código de retrieve_context).")
            print("   3. Verifica que Cloud Run tenga timeout configurado a más de 60 segundos.")
            print("   4. Prueba el retrieval service directamente (usa test_retrieval_service.py).")
        elif result.get("error") == "connection_error":
            print("\n🔍 SUGERENCIAS PARA ERROR DE CONEXIÓN:")
            print("   1. Verifica que la URL de la Azure Function sea correcta.")
            print("   2. Asegúrate de que la Azure Function esté en ejecución.")
            print("   3. Verifica que el código de autenticación (code=...) sea válido.")

    print("=" * 60)


if __name__ == "__main__":
    main()