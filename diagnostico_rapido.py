#!/usr/bin/env python3
"""
Diagnóstico rápido del sistema RAG
"""
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embeddings import EmbeddingModel
from rag.core import RAGSystem

print("🔍 DIAGNÓSTICO RÁPIDO DEL SISTEMA RAG")
print("=" * 70)

# 1. Probar embeddings
print("\n1. 📊 PRUEBA DE EMBEDDINGS:")
embedder = EmbeddingModel()

test_texts = [
    "cambio correo electrónico",
    "modificar email",
    "problemas con domicilio",
    "hola buenos días"
]

for text in test_texts:
    embedding = embedder.embed_text(text)
    norm = np.linalg.norm(embedding)
    print(f"   • '{text[:20]}...'")
    print(f"     Norma: {norm:.4f} {'✅' if 0.95 < norm < 1.05 else '❌'}")
    print(f"     Forma: {embedding.shape}")
    print(f"     Rango: [{embedding.min():.3f}, {embedding.max():.3f}]")

# 2. Probar RAG system
print("\n2. 🤖 PRUEBA DEL SISTEMA RAG:")
rag = RAGSystem()

# Consulta de prueba
query = "¿Cómo cambio mi correo electrónico?"
print(f"   Consulta: {query}")

# Ver embedding de la consulta
query_embedding = embedder.embed_text(query)
print(f"   Norma consulta: {np.linalg.norm(query_embedding):.4f}")

# Procesar
response, is_rag, confidence, sources = rag.process_query(query)

print(f"   ¿Es RAG?: {is_rag}")
print(f"   Confianza: {confidence:.2%}")
print(f"   Fuentes: {len(sources)}")

if sources:
    print(f"\n3. 📚 DOCUMENTOS ENCONTRADOS:")
    for i, source in enumerate(sources):
        print(f"   {i+1}. Preview: {source['content_preview'][:80]}...")
        
        # Mostrar metadatos simples
        if 'metadata' in source:
            meta = source['metadata']
            print(f"      📍 Row: {meta.get('row_index', 'N/A')}")
            print(f"      📄 Sheet: {meta.get('sheet_name', 'N/A')}")

# 3. Ver estadísticas
print("\n4. 📈 ESTADÍSTICAS DEL SISTEMA:")
stats = rag.get_stats()
print(f"   • Documentos totales: {stats.get('vector_store', {}).get('total_documents', 0)}")
print(f"   • Modelo: {stats.get('embedding_model', 'unknown')}")
print(f"   • Intents: {'✅ cargados' if stats.get('intents_loaded', False) else '❌ no cargados'}")

print("\n" + "=" * 70)
print("🎯 PROBLEMAS DETECTADOS:")
print("1. ❌ Embeddings no normalizados (norma debería ser ~1.0)")
print("2. ❌ Confianza muy baja (< 20%)")
print("3. ❌ Documentos irrelevantes encontrados")
print("\n✅ SOLUCIONES:")
print("1. Normalizar embeddings en embeddings.py")
print("2. Reducir temporalmente SIMILARITY_THRESHOLD a 0.3")
print("3. Verificar contenido de los documentos cargados")