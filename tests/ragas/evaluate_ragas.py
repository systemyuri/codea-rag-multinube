#!/usr/bin/env python3
"""
Script de evaluación RAGAS para CODEA RAG.
Uso: python evaluate_ragas.py [--sample N] [--threshold 0.7]
"""

import json
import os
import sys
import time
from typing import List, Dict, Any
import requests
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================

AZURE_FUNCTION_URL = "https://codea-orchestrator.azurewebsites.net/api/ask?code=APgUNXw0hbrLWtTjXHnXUU6JwAXKjZbeMMa9enOmNYW9AzFup1vvTA=="
QUESTIONS_FILE = "questions.json"
TIMEOUT_SECONDS = 120
SAMPLE_SIZE = 20  # Número de preguntas a evaluar (0 = todas)
THRESHOLD = 0.7   # Umbral mínimo para RAGAS

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def load_questions(file_path: str) -> List[Dict[str, Any]]:
    """Carga las preguntas desde un archivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    return [q for q in questions if q.get('active', True)]

def ask_question(question: str) -> Dict[str, Any]:
    """Envía una pregunta a la Azure Function y devuelve la respuesta."""
    payload = {"question": question}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "timeout", "answer": "ERROR: Timeout", "chunks": []}
    except Exception as e:
        return {"error": str(e), "answer": f"ERROR: {str(e)}", "chunks": []}

def extract_context(chunks: List[Dict]) -> str:
    """Extrae el texto de los chunks para formar el contexto."""
    if not chunks:
        return ""
    context_parts = []
    for c in chunks:
        content = c.get('content', '') or c.get('chunk_text', '') or c.get('text', '')
        article = c.get('article', '')
        if article:
            context_parts.append(f"[{article}] {content}")
        else:
            context_parts.append(content)
    return "\n\n".join(context_parts)

# ============================================================
# EVALUACIÓN CON RAGAS (requiere instalación)
# ============================================================

def evaluate_with_ragas(questions: List[Dict], sample_size: int = None) -> Dict:
    """
    Evalúa el sistema RAG usando la librería ragas.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import (
            context_relevancy,
            answer_relevancy,
            faithfulness
        )
        from datasets import Dataset
    except ImportError:
        print("❌ RAGAS no está instalado. Ejecuta:")
        print("   pip install ragas datasets")
        return None
    
    # Seleccionar muestra
    if sample_size and sample_size > 0 and sample_size < len(questions):
        import random
        sample = random.sample(questions, sample_size)
    else:
        sample = questions
    
    print(f"📊 Evaluando {len(sample)} preguntas con RAGAS...")
    
    results = []
    contexts_list = []
    answers_list = []
    ground_truths_list = []
    questions_list = []
    
    for i, q in enumerate(sample):
        question = q['question']
        expected = q.get('expectedAnswer', '')
        articles = q.get('expectedArticles', '')
        
        print(f"  [{i+1}/{len(sample)}] {question[:60]}...")
        
        # Llamar a la Azure Function
        response = ask_question(question)
        
        if 'error' in response:
            print(f"    ⚠️ Error: {response['error']}")
            answer = "ERROR"
            context = ""
        else:
            answer = response.get('answer', '')
            chunks = response.get('chunks', [])
            context = extract_context(chunks)
        
        answers_list.append(answer)
        contexts_list.append(context)
        ground_truths_list.append(expected)
        questions_list.append(question)
        
        results.append({
            "question": question,
            "answer": answer,
            "context": context,
            "expected": expected,
            "articles": articles,
            "chunks_count": len(chunks)
        })
    
    # Crear dataset para RAGAS
    dataset = Dataset.from_dict({
        "question": questions_list,
        "answer": answers_list,
        "contexts": [[c] for c in contexts_list],  # RAGAS espera lista de listas
        "ground_truth": ground_truths_list,
    })
    
    # Calcular métricas
    metrics = [context_relevancy, answer_relevancy, faithfulness]
    score = evaluate(dataset, metrics=metrics)
    
    # Extraer resultados
    result = {
        "context_relevancy": float(score["context_relevancy"]),
        "answer_relevancy": float(score["answer_relevancy"]),
        "faithfulness": float(score["faithfulness"]),
        "avg_score": float(score["context_relevancy"] + score["answer_relevancy"] + score["faithfulness"]) / 3,
        "sample_size": len(sample),
        "total_questions": len(questions),
        "details": results
    }
    
    return result

# ============================================================
# EVALUACIÓN SIMPLE (sin RAGAS)
# ============================================================

def evaluate_simple(questions: List[Dict], sample_size: int = None) -> Dict:
    """
    Evaluación simple basada en coincidencia de palabras clave (fallback).
    """
    import re
    from collections import Counter
    
    # Seleccionar muestra
    if sample_size and sample_size > 0 and sample_size < len(questions):
        import random
        sample = random.sample(questions, sample_size)
    else:
        sample = questions
    
    print(f"📊 Evaluando {len(sample)} preguntas (modo simple)...")
    
    results = []
    passed = 0
    total = 0
    
    def normalize_text(text: str) -> str:
        text = text.lower()
        # Eliminar tildes
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        # Eliminar caracteres especiales
        text = re.sub(r'[^a-z0-9\s.,;:()\-]', '', text)
        return text.strip()
    
    for i, q in enumerate(sample):
        question = q['question']
        expected = q.get('expectedAnswer', '')
        
        print(f"  [{i+1}/{len(sample)}] {question[:60]}...")
        
        response = ask_question(question)
        
        if 'error' in response:
            answer = "ERROR"
            success = False
        else:
            answer = response.get('answer', '')
            
            # Normalizar y comparar
            norm_answer = normalize_text(answer)
            norm_expected = normalize_text(expected)
            
            # Extraer palabras clave de la respuesta esperada
            keywords = set(norm_expected.replace(',', ' ').replace(';', ' ').split())
            keywords = {k for k in keywords if len(k) > 3}
            
            if not keywords:
                success = True
            else:
                found = sum(1 for kw in keywords if kw in norm_answer)
                success = found / len(keywords) >= 0.25
        
        results.append({
            "question": question,
            "answer": answer,
            "expected": expected,
            "success": success
        })
        
        if success:
            passed += 1
        total += 1
    
    return {
        "passed": passed,
        "total": total,
        "accuracy": passed / total if total > 0 else 0,
        "details": results,
        "method": "simple_keyword_match"
    }

# ============================================================
# GENERAR REPORTE
# ============================================================

def generate_report(result: Dict, output_file: str = "ragas-report.json"):
    """Genera un reporte en formato JSON y Markdown."""
    
    # Guardar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Generar Markdown
    md_file = output_file.replace('.json', '.md')
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 📊 Reporte de Evaluación RAGAS – CODEA RAG\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if "avg_score" in result:
            # Resultado RAGAS
            f.write("## 📌 Métricas RAGAS\n\n")
            f.write("| Métrica | Puntuación | ¿Cumple umbral (≥ 0.7)? |\n")
            f.write("|---------|------------|-------------------------|\n")
            for metric in ["context_relevancy", "answer_relevancy", "faithfulness"]:
                score = result.get(metric, 0)
                passes = "✅ Sí" if score >= 0.7 else "❌ No"
                f.write(f"| {metric.replace('_', ' ').title()} | {score:.3f} | {passes} |\n")
            f.write(f"| **Promedio** | **{result.get('avg_score', 0):.3f}** | **{'✅ Sí' if result.get('avg_score', 0) >= 0.7 else '❌ No'}** |\n\n")
            
            f.write(f"**Muestra evaluada:** {result.get('sample_size', 0)} preguntas\n")
            f.write(f"**Total de preguntas disponibles:** {result.get('total_questions', 0)}\n\n")
            
            if result.get('avg_score', 0) >= 0.7:
                f.write("✅ **El sistema cumple con el umbral mínimo de 0.7 exigido.**\n\n")
            else:
                f.write("⚠️ **El sistema NO cumple con el umbral mínimo de 0.7.**\n\n")
        else:
            # Resultado simple
            f.write("## 📌 Resultados de Validación\n\n")
            f.write(f"| Métrica | Valor |\n")
            f.write(f"|---------|-------|\n")
            f.write(f"| Preguntas aprobadas | {result.get('passed', 0)} |\n")
            f.write(f"| Total de preguntas | {result.get('total', 0)} |\n")
            f.write(f"| Precisión | {result.get('accuracy', 0):.2%} |\n")
            f.write(f"| Método | {result.get('method', 'desconocido')} |\n\n")
        
        # Detalles por pregunta
        f.write("## 📝 Detalles por Pregunta\n\n")
        f.write("| # | Pregunta | ¿Aprobada? |\n")
        f.write("|---|----------|------------|\n")
        for i, detail in enumerate(result.get('details', [])):
            question = detail.get('question', '')[:60]
            if len(detail.get('question', '')) > 60:
                question += "..."
            success = "✅ Sí" if detail.get('success', False) else "❌ No"
            f.write(f"| {i+1} | {question} | {success} |\n")
        
        f.write("\n---\n")
        f.write("*Reporte generado automáticamente por `evaluate_ragas.py`*\n")
    
    print(f"✅ Reporte guardado en: {output_file} y {md_file}")
    return md_file

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluación RAGAS para CODEA RAG")
    parser.add_argument("--sample", type=int, default=SAMPLE_SIZE, help="Número de preguntas a evaluar (0 = todas)")
    parser.add_argument("--threshold", type=float, default=THRESHOLD, help="Umbral mínimo para RAGAS")
    parser.add_argument("--questions", type=str, default=QUESTIONS_FILE, help="Archivo de preguntas")
    parser.add_argument("--output", type=str, default="ragas-report.json", help="Archivo de salida")
    parser.add_argument("--no-ragas", action="store_true", help="Usar evaluación simple en lugar de RAGAS")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 EVALUACIÓN RAGAS PARA CODEA RAG")
    print("=" * 60)
    
    # Cargar preguntas
    if not os.path.exists(args.questions):
        print(f"❌ No se encuentra el archivo: {args.questions}")
        sys.exit(1)
    
    questions = load_questions(args.questions)
    print(f"📚 Cargadas {len(questions)} preguntas activas.")
    
    if len(questions) == 0:
        print("❌ No hay preguntas activas.")
        sys.exit(1)
    
    sample_size = args.sample if args.sample > 0 else len(questions)
    
    # Evaluar
    if args.no_ragas:
        print("🔧 Usando modo de evaluación simple (sin RAGAS)")
        result = evaluate_simple(questions, sample_size)
    else:
        try:
            result = evaluate_with_ragas(questions, sample_size)
            if result is None:
                print("⚠️ Falló la evaluación con RAGAS. Usando modo simple...")
                result = evaluate_simple(questions, sample_size)
        except Exception as e:
            print(f"⚠️ Error en RAGAS: {e}")
            print("   Usando modo simple...")
            result = evaluate_simple(questions, sample_size)
    
    # Generar reporte
    generate_report(result, args.output)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    if "avg_score" in result:
        print("📊 RESULTADOS RAGAS")
        print(f"  Context Relevancy:   {result.get('context_relevancy', 0):.3f}")
        print(f"  Answer Relevancy:    {result.get('answer_relevancy', 0):.3f}")
        print(f"  Faithfulness:        {result.get('faithfulness', 0):.3f}")
        print(f"  PROMEDIO:            {result.get('avg_score', 0):.3f}")
        if result.get('avg_score', 0) >= args.threshold:
            print("  ✅ CUMPLE CON EL UMBRAL")
        else:
            print("  ❌ NO CUMPLE CON EL UMBRAL")
    else:
        print("📊 RESULTADOS DE VALIDACIÓN")
        print(f"  Aprobadas: {result.get('passed', 0)} / {result.get('total', 0)}")
        print(f"  Precisión: {result.get('accuracy', 0):.2%}")
    
    print(f"\n📄 Reporte completo: {args.output}")
    print("=" * 60)

if __name__ == "__main__":
    main()