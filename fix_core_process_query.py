# fix_core_process_query.py
import os

def fix_core_process_query():
    """Corrige el método process_query en core.py"""
    
    print("=== CORRECCIÓN PROCESS_QUERY EN CORE.PY ===\n")
    
    core_path = "rag/core.py"
    
    if not os.path.exists(core_path):
        print(f"✗ No existe: {core_path}")
        return
    
    print(f"Leyendo {core_path}...")
    
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el método process_query
    method_start = content.find("def process_query(self, query: str) -> Tuple[str, bool, float, list]:")
    
    if method_start == -1:
        print("✗ No se encontró el método process_query")
        return
    
    print("✓ Método process_query encontrado")
    
    # Extraer el método completo para analizarlo
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = len(content)
    
    method_content = content[method_start:method_end]
    
    # Buscar la sección de intents
    if "intent_results = self.vector_store.search_intents" in method_content:
        print("✓ Sección de intents encontrada")
        
        # Dividir el método en líneas para trabajar más fácil
        lines = content.split('\n')
        
        # Encontrar las líneas del método process_query
        in_process_query = False
        process_query_lines = []
        start_line = -1
        end_line = -1
        
        for i, line in enumerate(lines):
            if "def process_query(self, query: str)" in line:
                in_process_query = True
                start_line = i
                process_query_lines = [line]
            elif in_process_query:
                process_query_lines.append(line)
                # Buscar el final del método (cuando la indentación vuelve a 4 espacios o menos)
                if (line.strip() and 
                    not line.startswith(' ' * 8) and 
                    "def " in line and 
                    i > start_line + 10):
                    end_line = i
                    break
        
        if end_line == -1:
            end_line = len(lines)
        
        # Reconstruir el método con la corrección
        corrected_lines = []
        in_intent_section = False
        intent_section_start = -1
        
        for i in range(start_line, min(end_line, len(lines))):
            line = lines[i]
            
            # Buscar la sección de intents
            if "intent_results = self.vector_store.search_intents" in line:
                in_intent_section = True
                intent_section_start = i
            
            if in_intent_section and "if (intent_results['metadatas']" in line:
                # Encontró la verificación problemática
                print("✓ Encontrada verificación problemática de intents")
                
                # Reemplazar desde esta línea
                corrected_lines.append(line)  # La línea actual
                
                # Leer las siguientes líneas hasta encontrar el return
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("return "):
                    j += 1
                
                # Saltar las líneas problemáticas
                i = j - 1  # Ajustar el índice
                in_intent_section = False
                
                # Insertar la versión corregida
                corrected_intent_section = '''        # Verificar si hay match de intent
        try:
            if (intent_results and 
                intent_results.get('metadatas') and 
                len(intent_results['metadatas']) > 0 and
                len(intent_results['metadatas'][0]) > 0):
                
                # Es un intent conocido
                metadata = intent_results['metadatas'][0][0]
                response = self.generator.generate_from_intent(metadata)
                return response, False, 0.9, []
        except Exception as e:
            logger.warning(f"Error verificando intents: {e}")
            # Continuar con RAG si hay error'''
                
                corrected_lines.append(corrected_intent_section)
                
            elif not in_intent_section:
                corrected_lines.append(line)
        else:
            corrected_lines.append(line)
        
        # Si no encontramos la sección problemática, hacer reemplazo directo
        if intent_section_start == -1:
            print("⚠️ No se encontró la sección específica, intentando reemplazo directo")
            
            # Buscar el patrón problemático
            problem_pattern = '''    # Verificar si hay match de intent
    if (intent_results['metadatas'] and 
        intent_results['metadatas'][0] and 
        len(intent_results['metadatas'][0]) > 0):
        
        # Es un intent conocido
        metadata = intent_results['metadatas'][0][0]
        response = self.generator.generate_from_intent(metadata)
        return response, False, 0.9, []'''
            
            if problem_pattern in content:
                corrected_pattern = '''    # Verificar si hay match de intent
    try:
        if (intent_results and 
            intent_results.get('metadatas') and 
            len(intent_results['metadatas']) > 0 and
            len(intent_results['metadatas'][0]) > 0):
            
            # Es un intent conocido
            metadata = intent_results['metadatas'][0][0]
            response = self.generator.generate_from_intent(metadata)
            return response, False, 0.9, []
    except Exception as e:
        logger.warning(f"Error verificando intents: {e}")
        # Continuar con RAG si hay error'''
                
                content = content.replace(problem_pattern, corrected_pattern)
                
                # Guardar
                backup_path = core_path + ".backup_process_query"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                with open(core_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✓ Reemplazo directo completado")
                return
        
        # Si usamos el método de reconstrucción
        if corrected_lines:
            # Reconstruir el contenido
            new_content = '\n'.join(lines[:start_line] + corrected_lines + lines[end_line:])
            
            # Hacer backup
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{core_path}.backup_{timestamp}"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Backup creado: {backup_path}")
            
            # Guardar corrección
            with open(core_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✓ Método process_query corregido")
    else:
        print("✗ No se encontró la sección de intents en process_query")
        return

def create_simple_test():
    """Crea un test simple para verificar la corrección"""
    
    print("\n=== CREANDO TEST DE VERIFICACIÓN ===\n")
    
    test_content = '''import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_core_fix():
    """Prueba la corrección del core.py"""
    print("=== TEST CORRECCIÓN CORE.PY ===\\n")
    
    from rag.core import RAGSystem
    
    # Crear sistema
    rag = RAGSystem()
    
    # Cargar intents
    intents_path = "data/vector_store/intents.json"
    if os.path.exists(intents_path):
        rag.load_intents(intents_path)
        print(f"✓ Intents cargados: {rag.intents_loaded}")
    else:
        print(f"✗ No existe: {intents_path}")
        return
    
    # Probar consultas
    test_cases = [
        ("hola", "SALUDO - debería usar intent"),
        ("buenos días", "SALUDO - debería usar intent"),
        ("adiós", "DESPEDIDA - debería usar intent"),
        ("¿Cuánto dura el módulo?", "CONTENIDO - debería usar RAG o fallback"),
        ("xkzpd qwerty", "SIN SENTIDO - debería usar fallback"),
    ]
    
    print("\\nProbando consultas:\\n")
    
    for query, description in test_cases:
        print(f"Query: '{query}'")
        print(f"Descripción: {description}")
        
        try:
            response, is_rag, confidence, sources = rag.process_query(query)
            
            print(f"Respuesta: {response[:80]}...")
            print(f"is_rag: {is_rag}")
            print(f"confidence: {confidence:.3f}")
            
            # Verificar
            if "Error" in response and "tuve un problema" in response:
                print("❌ ERROR: La corrección no funcionó")
            elif not is_rag and ("Hola" in response or "Buen día" in response or "Hasta luego" in response):
                print("✅ CORRECTO: Usó intent apropiadamente")
            elif is_rag:
                print("ℹ️  Usó RAG")
            else:
                print("ℹ️  Usó fallback")
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)
    
    print("\\n=== FIN TEST ===")

if __name__ == "__main__":
    test_core_fix()
'''
    
    test_path = "test_core_fix.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✓ Test creado: {test_path}")
    
    print("\n📋 INSTRUCCIONES:")
    print("1. Ejecuta: python fix_core_process_query.py")
    print("2. Luego: python test_core_fix.py")
    print("3. Si funciona, prueba: python debug_intents_fixed_corrected.py")
    print("4. Finalmente reinicia la API: python -m api.main")

if __name__ == "__main__":
    fix_core_process_query()
    create_simple_test()