#!/usr/bin/env python3
"""
Script para probar el endpoint /retrieve del servicio de retrieval en Cloud Run.
Uso: python test_retrieval_service.py
"""

import requests
import json
import random
import sys
import time

# ============================================================
# CONFIGURACIÓN - ACTUALIZA CON TU URL REAL
# ============================================================

# URL de tu retrieval service en Cloud Run
RETRIEVAL_URL = "https://retrieval-service-flzlnepzjq-uc.a.run.app/retrieve"

# Número de dimensiones del embedding (usas 1536)
VECTOR_DIM = 1536

# Timeout en segundos
TIMEOUT_SECONDS = 30

# ============================================================
# FIN DE LA CONFIGURACIÓN
# ============================================================

def generate_random_vector(dim: int) -> list:
    """Genera un vector aleatorio de dimensión dim (simula un embedding)."""
    return [random.random() for _ in range(dim)]

def test_retrieval_service(vector: list, limit: int = 5, filtros: dict = None):
    """Envía una solicitud al retrieval service y mide el tiempo de respuesta."""
    payload = {"vector": vector, "limit": limit}
    if filtros:
        payload["filtros"] = filtros

    headers = {"Content-Type": "application/json"}

    print(f"\n🚀 Enviando solicitud al retrieval service...")
    print(f"🔗 URL: {RETRIEVAL_URL}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print(f"⏱️  Timeout: {TIMEOUT_SECONDS} segundos")
    print("-" * 60)

    start_time = time.time()

    try:
        response = requests.post(
            RETRIEVAL_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )

        elapsed = time.time() - start_time
        print(f"⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")

        # Intentar parsear la respuesta como JSON
        try:
            data = response.json()
            print("\n📦 Respuesta JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        except json.JSONDecodeError:
            print("\n📄 Respuesta (texto plano):")
            print(response.text[:500])

        if response.status_code == 200:
            print("\n✅ ¡El retrieval service respondió correctamente!")
        else:
            print(f"\n⚠️  El retrieval service respondió con error {response.status_code}")

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "data": data if 'data' in locals() else None,
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR: Timeout después de {elapsed:.2f} segundos")
        print(f"   El retrieval service no respondió en {TIMEOUT_SECONDS} segundos.")
        print("   Posibles causas:")
        print("   - El servicio está caído o no responde.")
        print("   - La conexión a la base de datos (AlloyDB) está fallando.")
        print("   - Cold start (la primera petición tarda mucho).")
        print("   - Timeout configurado en Cloud Run es menor que {TIMEOUT_SECONDS}.")
        return {"success": False, "error": "timeout", "elapsed": elapsed}

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR de conexión: {e}")
        print("   No se pudo conectar al retrieval service.")
        print("   Verifica que la URL sea correcta y que el servicio esté activo.")
        return {"success": False, "error": "connection_error", "details": str(e)}

    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")
        return {"success": False, "error": "unexpected_error", "details": str(e)}

def main():
    print("=" * 60)
    print("🧪 TEST DEL RETRIEVAL SERVICE (CLOUD RUN)")
    print("=" * 60)

    # Generar un vector aleatorio
    vector = generate_random_vector(VECTOR_DIM)
    print(f"✅ Vector generado (primeros 5 valores): {vector[:5]}...")

    # 1. Prueba sin filtros
    print("\n" + "=" * 60)
    print("🔹 PRUEBA 1: Sin filtros")
    result1 = test_retrieval_service(vector, limit=5)

    # 2. Prueba con filtros (si quieres)
    print("\n" + "=" * 60)
    print("🔹 PRUEBA 2: Con filtros (norm_code = 'LEY 27337')")
    filtros = {"norm_code": "LEY 27337"}
    result2 = test_retrieval_service(vector, limit=5, filtros=filtros)

    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print(f"  Prueba 1 (sin filtros): {'✅ Éxito' if result1.get('success') else '❌ Falló'}")
    print(f"  Prueba 2 (con filtros): {'✅ Éxito' if result2.get('success') else '❌ Falló'}")

if __name__ == "__main__":
    main()