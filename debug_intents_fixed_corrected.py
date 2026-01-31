# debug_intents_fixed_corrected.py
import sys
import os
import json
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_intents_system():
    """Diagnóstico del sistema de intents"""
    print("=== DIAGNÓSTICO SISTEMA INTENTS ===\n")
    
    try:
        # 1. Cargar sistema RAG
        from rag.core import RAGSystem
        rag = RAGSystem()
        print("✓ Sistema RAG cargado")
        
        # 2. Cargar intents
        print("\n2. Cargando intents...")
        intents_path = "data/vector_store/intents.json"
        print(f"   Ruta: {os.path.abspath(intents_path)}")
        print(f"   Existe: {os.path.exists(intents_path)}")
        
        if os.path.exists(intents_path):
            with open(intents_path, 'r', encoding='utf-8') as f:
                intents_data = json.load(f)
                print(f"   Número de intents: {len(intents_data.get('intents', []))}")
                
                # Mostrar algunos intents
                print("\n   Primeros intents:")
                for i, intent in enumerate(intents_data.get('intents', [])[:3]):
                    print(f"   {i+1}. Tag: {intent.get('tag', 'N/A')}")
                    print(f"      Patrones: {len(intent.get('patterns', []))}")
                    print(f"      Respuestas: {len(intent.get('responses', []))}")
        else:
            print("   ✗ Archivo no encontrado")
        
        # 3. Intentar cargar intents
        print("\n3. Intentando cargar intents en el sistema...")
        rag.load_intents(intents_path)
        print(f"   Intents cargados: {rag.intents_loaded}")
        
        # 4. Examinar el vector store
        print("\n4. Examinando vector store...")
        print(f"   Número de documentos: {len(rag.vector_store.documents)}")
        print(f"   Intents cargados en vector store: {len(rag.vector_store.intents.get('intents', []))}")
        
        # 5. Probar search_intents directamente CON TEXTO
        print("\n5. Probando search_intents directamente...")
        
        test_queries = [
            "hola",
            "buenos días",
            "¿cómo estás?",
            "adiós",
            "gracias por la ayuda"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            # Generar embedding (solo para referencia)
            query_embedding = rag.embedder.embed_text(query)
            print(f"   Embedding generado: shape={query_embedding.shape}")
            
            # Buscar intents CON TEXTO
            intent_results = rag.vector_store.search_intents(
                query_text=query, 
                query_embedding=query_embedding, 
                top_k=1
            )
            
            print(f"   Resultados: {intent_results}")
            
            if (intent_results['metadatas'] and 
                intent_results['metadatas'][0] and 
                len(intent_results['metadatas'][0]) > 0):
                
                metadata = intent_results['metadatas'][0][0]
                print(f"   ✅ Intent encontrado: {metadata.get('tag', 'N/A')}")
                print(f"   Match type: {metadata.get('match_type', 'N/A')}")
            else:
                print("   ❌ No se encontró intent")
        
        # 6. Probar process_query completo
        print("\n6. Probando process_query completo...")
        
        test_queries = [
            ("hola", "DEBERÍA SER INTENT"),
            ("buenos días", "DEBERÍA SER INTENT"),
            ("hola buenas, tengo una duda", "DEBERÍA SER INTENT (patrón exacto)"),
            ("¿Cuánto dura el módulo?", "DEBERÍA SER RAG O FALLBACK"),
            ("¿Quién ganó el mundial?", "DEBERÍA SER FALLBACK"),
        ]
        
        for query, expected in test_queries:
            print(f"\n   Query: '{query}'")
            print(f"   Esperado: {expected}")
            
            response, is_rag, confidence, sources = rag.process_query(query)
            
            print(f"   Respuesta: {response[:100]}...")
            print(f"   is_rag: {is_rag}")
            print(f"   confidence: {confidence:.3f}")
            print(f"   sources: {len(sources)}")
            
            # Análisis
            if "Hola" in response or "Buen día" in response or "gracias" in response.lower():
                print("   ✅ Detectado como intent (saludo/despedida/agradecimiento)")
                if is_rag:
                    print("   ⚠️ Pero es RAG, debería ser intent")
                else:
                    print("   ✅ Correcto: Es intent")
            elif "No encontré" in response or "fuera del alcance" in response:
                print("   ✅ Detectado como fallback")
            elif is_rag:
                print("   🔍 Detectado como respuesta RAG")
            else:
                print("   ❓ Tipo de respuesta no identificado")
                
    except Exception as e:
        print(f"✗ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_intents_system()