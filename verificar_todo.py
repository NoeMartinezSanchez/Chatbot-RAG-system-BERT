#!/usr/bin/env python3
"""
Verificación completa del sistema
"""
import sys
import os

print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA")
print("=" * 60)

# 1. Verificar estructura de directorios
print("\n📁 ESTRUCTURA DE DIRECTORIOS:")
required_dirs = ["api", "config", "rag", "static", "data/vector_store"]
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"  ✅ {dir_path}/")
    else:
        print(f"  ❌ {dir_path}/ - NO EXISTE")

# 2. Verificar archivos críticos
print("\n📄 ARCHIVOS CRÍTICOS:")
critical_files = [
    "api/main.py",
    "config/settings.py", 
    "rag/core.py",
    "rag/retriever.py",
    "rag/embeddings.py",
    "static/index.html",
    ".env"
]
for file_path in critical_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"  ✅ {file_path} ({size} bytes)")
    else:
        print(f"  ❌ {file_path} - NO EXISTE")

# 3. Verificar imports
print("\n🔗 VERIFICANDO IMPORTS:")
try:
    from config.settings import settings, print_config_summary
    print("  ✅ config.settings - OK")
    
    # Mostrar configuración
    print("\n⚙️  CONFIGURACIÓN ACTUAL:")
    print(f"  API: {settings.API_HOST}:{settings.API_PORT}")
    print(f"  Modelo: {settings.EMBEDDING_MODEL}")
    print(f"  Top K: {settings.TOP_K_RESULTS}")
    print(f"  FAISS Persist Dir: {settings.FAISS_PERSIST_DIR}")
    
except Exception as e:
    print(f"  ❌ config.settings - ERROR: {e}")

# 4. Verificar módulos RAG
modules_to_test = [
    ("rag.retriever", "VectorStoreFAISS"),
    ("rag.core", "RAGSystem"),
    ("rag.embeddings", "EmbeddingModel"),
]

print("\n🤖 VERIFICANDO MÓDULOS RAG:")
for module_name, class_name in modules_to_test:
    try:
        exec(f"from {module_name} import {class_name}")
        print(f"  ✅ {module_name}.{class_name} - OK")
    except Exception as e:
        print(f"  ❌ {module_name}.{class_name} - ERROR: {e}")

# 5. Verificar API
print("\n🌐 VERIFICANDO API:")
try:
    from api.main import app
    print("  ✅ api.main.app - OK")
    
    # Verificar endpoints configurados
    routes = [route.path for route in app.routes]
    print(f"  📍 Endpoints encontrados: {len(routes)}")
    for route in routes[:5]:  # Mostrar primeros 5
        print(f"    • {route}")
    
except Exception as e:
    print(f"  ❌ api.main - ERROR: {e}")

print("\n" + "=" * 60)
print("🎯 INSTRUCCIONES FINALES:")
print("1. Si hay ❌, corrige esos errores primero")
print("2. Si todo ✅, ejecuta: python -m api.main")
print("3. Abre en navegador:")
print("   • Interfaz: http://localhost:8000")
print("   • API Docs: http://localhost:8000/docs")
print("=" * 60)