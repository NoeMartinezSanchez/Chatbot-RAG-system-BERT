# fix_intents_search.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_intents_search():
    """Corrige el sistema de búsqueda de intents"""
    
    print("=== CORRECCIÓN BÚSQUEDA INTENTS ===\n")
    
    # 1. Corregir retriever.py
    retriever_path = "rag/retriever.py"
    
    if os.path.exists(retriever_path):
        print(f"1. Corrigiendo {retriever_path}...")
        
        with open(retriever_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar el método search_intents
        if "def search_intents(self, query_embedding: np.ndarray, top_k: int = 1) -> Dict:" in content:
            # Reemplazar con versión corregida
            new_method = '''def search_intents(self, query_text: str = None, query_embedding: np.ndarray = None, top_k: int = 1) -> Dict:
        """
        Buscar intents similares usando matching por texto.
        
        Args:
            query_text: Texto de la consulta (obligatorio para matching)
            query_embedding: Embedding de la consulta (no usado en esta implementación)
            top_k: Número de resultados a retornar
        
        Returns:
            Diccionario con formato compatible con ChromaDB
        """
        if not self.intents.get("intents"):
            return {'distances': [[]], 'metadatas': [[]]}
        
        if not query_text:
            # Sin texto, no podemos hacer matching
            return {'distances': [[]], 'metadatas': [[]]}
        
        query_lower = query_text.lower().strip()
        results = []
        distances = []
        
        # Buscar en todos los intents
        for intent in self.intents["intents"]:
            tag = intent.get("tag", "").lower()
            patterns = [p.lower() for p in intent.get("patterns", [])]
            
            # 1. Verificar si la query contiene el tag
            tag_match = tag in query_lower if tag else False
            
            # 2. Verificar si coincide con algún patrón
            pattern_match = False
            for pattern in patterns:
                if pattern in query_lower or query_lower in pattern:
                    pattern_match = True
                    break
            
            # 3. Verificar palabras clave comunes
            keywords_match = False
            common_keywords = {
                "saludo": ["hola", "buenos", "buenas", "saludos", "qué tal", "cómo estás"],
                "despedida": ["adiós", "hasta luego", "chao", "bye", "nos vemos"],
                "ayuda": ["ayuda", "ayúdame", "asistencia", "soporte"],
                "gracias": ["gracias", "agradecido", "agradezco"],
            }
            
            for keyword_list in common_keywords.values():
                if any(keyword in query_lower for keyword in keyword_list):
                    keywords_match = True
                    break
            
            # Si hay algún match
            if tag_match or pattern_match or keywords_match:
                # Calcular "distancia" (0 = perfect match, 1 = no match)
                if pattern_match:  # Coincidencia exacta con patrón
                    distance = 0.1
                elif tag_match:    # Coincidencia con tag
                    distance = 0.3
                else:              # Coincidencia con keywords
                    distance = 0.5
                
                results.append({
                    "tag": intent.get("tag", ""),
                    "responses": intent.get("responses", []),
                    "patterns": intent.get("patterns", []),
                    "context": intent.get("context", ""),
                    "match_type": "pattern" if pattern_match else "tag" if tag_match else "keyword"
                })
                distances.append(distance)
        
        # Ordenar por distancia (menor = mejor match)
        if results:
            sorted_results = sorted(zip(results, distances), key=lambda x: x[1])
            results = [r for r, _ in sorted_results[:top_k]]
            distances = [d for _, d in sorted_results[:top_k]]
        
        return {
            'distances': [distances],
            'metadatas': [results]
        }'''
        
            # Reemplazar el método
            import re
            pattern = r'def search_intents\(self, query_embedding: np\.ndarray, top_k: int = 1\) -> Dict:.*?(?=\n    def|\n\n|\Z)'
            corrected_content = re.sub(pattern, new_method, content, flags=re.DOTALL)
            
            # Hacer backup
            backup_path = retriever_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✓ Backup creado: {backup_path}")
            
            # Guardar corrección
            with open(retriever_path, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            
            print("   ✓ Método search_intents corregido")
        else:
            print("   ✗ No se encontró el método search_intents original")
    else:
        print(f"✗ No existe: {retriever_path}")
    
    # 2. Corregir core.py
    core_path = "rag/core.py"
    
    if os.path.exists(core_path):
        print(f"\n2. Corrigiendo {core_path}...")
        
        with open(core_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la llamada a search_intents
        if "intent_results = self.vector_store.search_intents(" in content:
            # Reemplazar con versión corregida
            old_line = "intent_results = self.vector_store.search_intents(query_embedding, top_k=1)"
            new_line = "intent_results = self.vector_store.search_intents(query_text=query, query_embedding=query_embedding, top_k=1)"
            
            corrected_content = content.replace(old_line, new_line)
            
            # Hacer backup
            backup_path = core_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✓ Backup creado: {backup_path}")
            
            # Guardar corrección
            with open(core_path, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            
            print("   ✓ Llamada a search_intents corregida")
        else:
            print("   ✗ No se encontró la llamada a search_intents")
    else:
        print(f"✗ No existe: {core_path}")
    
    # 3. Crear test de verificación
    print("\n3. Creando test de verificación...")
    
    test_content = '''import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fixed_intents():
    """Prueba el sistema de intents corregido"""
    print("=== TEST INTENTS CORREGIDO ===\\n")
    
    # 1. Cargar sistema
    from rag.core import RAGSystem
    rag = RAGSystem()
    
    # 2. Cargar intents
    intents_path = "data/vector_store/intents.json"
    if os.path.exists(intents_path):
        rag.load_intents(intents_path)
        print(f"✓ Intents cargados desde: {intents_path}")
    else:
        print(f"✗ No existe: {intents_path}")
        return
    
    # 3. Probar diferentes consultas
    test_cases = [
        # (query, debería_ser_intent, descripción)
        ("hola", True, "Saludo simple"),
        ("buenos días", True, "Saludo formal"),
        ("hola buenas, tengo una duda", True, "Patrón exacto del intent"),
        ("buen día, necesito ayuda con el módulo", True, "Otro patrón exacto"),
        ("hola, soy nuevo en el propedéutico", True, "Patrón exacto"),
        ("adiós", True, "Despedida"),
        ("¿cómo estás?", True, "Saludo informal"),
        ("gracias por la ayuda", True, "Agradecimiento"),
        ("¿Cuánto dura el módulo?", False, "Pregunta sobre contenido"),
        ("¿Qué es el módulo propedéutico?", False, "Pregunta conceptual"),
        ("¿Quién ganó el mundial?", False, "Pregunta fuera de contexto"),
        ("xkzpd qwerty", False, "Texto sin sentido"),
    ]
    
    print("\\nProbando consultas:\\n")
    
    correct_count = 0
    total_count = len(test_cases)
    
    for query, should_be_intent, description in test_cases:
        print(f"Query: '{query}'")
        print(f"Descripción: {description}")
        
        response, is_rag, confidence, sources = rag.process_query(query)
        
        print(f"Respuesta: {response[:80]}...")
        print(f"is_rag: {is_rag} (debería ser {not should_be_intent})")
        print(f"confidence: {confidence:.3f}")
        
        # Verificar
        is_intent_response = not is_rag and ("Hola" in response or "Buen día" in response or "gracias" in response.lower())
        
        if should_be_intent == is_intent_response:
            print("✅ CORRECTO")
            correct_count += 1
        else:
            print("❌ INCORRECTO")
            if should_be_intent:
                print("   Debería haber sido intent pero no lo fue")
            else:
                print("   No debería haber sido intent pero lo fue")
        
        print("-" * 60)
    
    accuracy = correct_count / total_count * 100
    print(f"\\nResultado: {correct_count}/{total_count} correctos ({accuracy:.1f}%)")
    
    if accuracy >= 80:
        print("\\n🎉 ¡EL SISTEMA DE INTENTS FUNCIONA CORRECTAMENTE!")
        print("\\nAhora puedes cargar documentos al RAG y probar preguntas de contenido.")
    else:
        print("\\n⚠️  El sistema necesita más ajustes.")

if __name__ == "__main__":
    test_fixed_intents()
'''
    
    test_path = "test_intents_fixed.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✓ Test creado: {test_path}")
    
    print("\n📋 INSTRUCCIONES:")
    print("1. Ejecuta: python fix_intents_search.py")
    print("2. Luego: python debug_intents_fixed.py")
    print("3. Luego: python test_intents_fixed.py")
    print("4. Si todo funciona, reinicia la API: python -m api.main")

if __name__ == "__main__":
    fix_intents_search()