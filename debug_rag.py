from rag.core import RAGSystem
import numpy as np

rag = RAGSystem()

# Probar una consulta
query = "¿Cómo cambio mi correo?"
print(f"📝 Consulta: {query}")

# 1. Ver embedding
embedding = rag.embedder.embed_text(query)
print(f"🔢 Embedding shape: {embedding.shape}")
print(f"🔢 Norma del embedding: {np.linalg.norm(embedding):.3f}")

# 2. Procesar
response, is_rag, confidence, sources = rag.process_query(query)
print(f"🤖 Respuesta: {response[:100]}...")
print(f"🎯 Es RAG: {is_rag}")
print(f"📊 Confianza: {confidence:.2%}")

# 3. Ver fuentes
if sources:
    print(f"📚 Fuentes: {len(sources)}")
    for i, source in enumerate(sources):
        print(f"  {i+1}. {source['content_preview']}")