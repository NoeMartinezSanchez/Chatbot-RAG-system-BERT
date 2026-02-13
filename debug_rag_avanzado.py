#!/usr/bin/env python3
"""
Sistema de Debug Avanzado para RAG - Prepa en Línea SEP
Mide performance antes/después de mejoras
"""
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, List, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir ruta del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RAGDebugger:
    """Debugger avanzado para sistema RAG"""
    
    def __init__(self):
        from rag.core import RAGSystem
        from rag.embeddings import EmbeddingModel
        
        self.rag = RAGSystem()
        self.embedder = EmbeddingModel()
        self.results = []
        
        # Crear carpeta debug si no existe
        self.debug_dir = Path("debug")
        self.debug_dir.mkdir(exist_ok=True)
        
        # Timestamp para identificación
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🔍 DEBUGGER RAG INICIALIZADO - {self.timestamp}")
        print("=" * 70)
    
    def test_query(self, query: str, test_name: str = "default"):
        """Probar una consulta específica"""
        print(f"\n🧪 PRUEBA: '{test_name}'")
        print(f"📝 Consulta: {query}")
        print("-" * 50)
        
        # Medir tiempo
        start_time = time.time()
        
        # 1. Analizar embedding
        embedding_start = time.time()
        embedding = self.embedder.embed_text(query)
        embedding_time = time.time() - embedding_start
        
        # 2. Procesar consulta completa
        process_start = time.time()
        response, is_rag, confidence, sources = self.rag.process_query(query)
        process_time = time.time() - process_start
        
        # 3. Obtener estadísticas del sistema
        stats = self.rag.get_stats()
        
        # 4. Calcular métricas del embedding
        embedding_norm = np.linalg.norm(embedding)
        embedding_mean = np.mean(embedding)
        embedding_std = np.std(embedding)
        
        # 5. Información detallada de búsqueda
        search_details = self._get_search_details(query, embedding)
        
        # Preparar resultado
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "query": query,
            
            # Tiempos
            "embedding_time_ms": round(embedding_time * 1000, 2),
            "process_time_ms": round(process_time * 1000, 2),
            "total_time_ms": round((time.time() - start_time) * 1000, 2),
            
            # Resultados
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            "is_rag_response": is_rag,
            "confidence_percent": round(confidence * 100, 2),
            "sources_count": len(sources),
            
            # Embedding metrics
            "embedding_norm": round(embedding_norm, 4),
            "embedding_mean": round(embedding_mean, 4),
            "embedding_std": round(embedding_std, 4),
            "embedding_shape": embedding.shape,
            
            # Sistema
            "total_documents": stats.get("vector_store", {}).get("total_documents", 0),
            "embedding_model": stats.get("embedding_model", "unknown"),
            "intents_loaded": stats.get("intents_loaded", False),
            
            # Detalles adicionales
            "sources_details": [self._format_source(s) for s in sources],
            "search_details": search_details,
            "full_response": response
        }
        
        self.results.append(result)
        
        # Mostrar en terminal
        self._print_result(result)
        
        return result
    
    def _get_search_details(self, query: str, query_embedding: np.ndarray) -> Dict:
        """Obtener detalles de la búsqueda (si es posible)"""
        try:
            # Buscar documentos directamente para obtener distancias
            from rag.retriever import VectorStoreFAISS
            
            # Necesitamos acceder al vector store directamente
            vector_store = self.rag.vector_store
            
            if hasattr(vector_store, 'search_documents'):
                results = vector_store.search_documents(query_embedding, top_k=5)
                
                if results['distances'] and results['distances'][0]:
                    distances = results['distances'][0]
                    similarities = [1/(1+d) if d>0 else 1.0 for d in distances]
                    
                    return {
                        "distances": [round(d, 4) for d in distances],
                        "similarities": [round(s*100, 2) for s in similarities],
                        "documents_found": len(results['documents'][0]) if results['documents'] else 0,
                        "best_similarity": round(max(similarities)*100, 2) if similarities else 0
                    }
        except Exception as e:
            logger.warning(f"No se pudieron obtener detalles de búsqueda: {e}")
        
        return {"error": "No disponible"}
    
    def _format_source(self, source: Dict) -> Dict:
        """Formatear fuente para guardar"""
        return {
            "content_preview": source.get("content_preview", "")[:100],
            "metadata": json.dumps(source.get("metadata", {}), ensure_ascii=False)[:200]
        }
    
    def _print_result(self, result: Dict):
        """Mostrar resultado en terminal de forma organizada"""
        
        print(f"⏱️  TIEMPOS:")
        print(f"   • Embedding: {result['embedding_time_ms']} ms")
        print(f"   • Proceso: {result['process_time_ms']} ms")
        print(f"   • Total: {result['total_time_ms']} ms")
        
        print(f"\n📊 EMBEDDING:")
        print(f"   • Norma: {result['embedding_norm']}")
        print(f"   • Media: {result['embedding_mean']}")
        print(f"   • Desv. Std: {result['embedding_std']}")
        print(f"   • Shape: {result['embedding_shape']}")
        
        print(f"\n🎯 RESULTADO:")
        print(f"   • ¿Es RAG?: {'✅ SÍ' if result['is_rag_response'] else '❌ NO'}")
        print(f"   • Confianza: {result['confidence_percent']}%")
        print(f"   • Fuentes encontradas: {result['sources_count']}")
        
        print(f"\n📝 RESPUESTA:")
        print(f"   {result['response_preview']}")
        
        if result['sources_count'] > 0:
            print(f"\n📚 FUENTES:")
            for i, source in enumerate(result['sources_details']):
                print(f"   {i+1}. {source['content_preview']}")
                # Mostrar metadatos si existen
                try:
                    metadata = json.loads(source['metadata']) if source['metadata'] else {}
                except json.JSONDecodeError:
                    metadata = {"error": "metadata no es JSON válido"}
                if metadata:
                    print(f"      📍 Row: {metadata.get('row_index', 'N/A')}")
                    print(f"      📄 Sheet: {metadata.get('sheet_name', 'N/A')}")
        
        if 'search_details' in result and 'best_similarity' in result['search_details']:
            print(f"\n🔍 BÚSQUEDA:")
            print(f"   • Mejor similitud: {result['search_details']['best_similarity']}%")
            if 'distances' in result['search_details']:
                distances = result['search_details']['distances']
                print(f"   • Distancias top 3: {distances[:3] if len(distances) >= 3 else distances}")
        
        print(f"\n📈 SISTEMA:")
        print(f"   • Documentos totales: {result['total_documents']}")
        print(f"   • Modelo: {result['embedding_model']}")
        print(f"   • Intents cargados: {'✅' if result['intents_loaded'] else '❌'}")
        
        print("\n" + "=" * 70)
    
    def run_test_suite(self):
        """Ejecutar suite de pruebas BASADA EN TUS DATOS REALES"""
        print("\n🚀 EJECUTANDO SUITE DE PRUEBAS ESPECÍFICA")
        print("=" * 70)
    
        test_queries = [
            # Preguntas DIRECTAMENTE en tus datos
            ("¿Cómo cambio mi correo electrónico?", "cambio_correo_directo"),
            ("Necesito actualizar mi email registrado", "actualizacion_email"),
            ("Me equivoqué de correo al registrarme", "correo_equivocado"),
            ("Olvidé mi contraseña de la cuenta", "olvido_contrasena"),
            ("No puedo acceder con mi correo institucional", "acceso_correo_institucional"),
            ("Quiero recuperar mi usuario y contraseña", "recuperar_credenciales"),
        
            # Temas específicos de tus clusters
            ("Problemas con el registro en la plataforma", "problemas_registro"),
            ("Ya tengo un registro previo como alumno", "registro_previo"),
            ("Quiero retomar mis estudios en prepa en línea", "reingreso_estudios"),
            ("Cómo me reincorporo al programa", "reincorporacion"),
        
            # Verificación de respuestas institucionales
            ("Qué documentos necesito para inscripción", "documentacion_inscripcion"),
            ("Cuál es el proceso para bajas definitivas", "bajas_definitivas"),
            ("SLA para soporte técnico", "sla_soporte"),
        
            # Casos para intents
            ("Hola", "saludo_simple"),
            ("Nos vemos", "saludo_despedida"),
        ]

        for query, name in test_queries:
            self.test_query(query, name)
            time.sleep(0.5)

    
    def save_results(self, filename: str = None):
        """Guardar resultados en Excel y JSON"""
        if not self.results:
            print("❌ No hay resultados para guardar")
            return
        
        if filename is None:
            filename = f"rag_debug_{self.timestamp}"
        
        # Guardar en Excel
        excel_path = self.debug_dir / f"{filename}.xlsx"
        
        # Preparar DataFrame para Excel
        df_data = []
        for result in self.results:
            row = {
                "timestamp": result["timestamp"],
                "test_name": result["test_name"],
                "query": result["query"],
                "embedding_time_ms": result["embedding_time_ms"],
                "process_time_ms": result["process_time_ms"],
                "total_time_ms": result["total_time_ms"],
                "is_rag_response": result["is_rag_response"],
                "confidence_percent": result["confidence_percent"],
                "sources_count": result["sources_count"],
                "embedding_norm": result["embedding_norm"],
                "embedding_mean": result["embedding_mean"],
                "embedding_std": result["embedding_std"],
                "total_documents": result["total_documents"],
                "response_preview": result["response_preview"],
            }
            
            # Añadir detalles de búsqueda si existen
            if "search_details" in result:
                sd = result["search_details"]
                row["best_similarity"] = sd.get("best_similarity", 0)
                row["documents_found"] = sd.get("documents_found", 0)
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Crear Excel con múltiples hojas
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Hoja 1: Resumen
            df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja 2: Respuestas completas
            full_responses = []
            for result in self.results:
                full_responses.append({
                    "test_name": result["test_name"],
                    "query": result["query"],
                    "full_response": result["full_response"],
                    "confidence": result["confidence_percent"]
                })
            pd.DataFrame(full_responses).to_excel(writer, sheet_name='Respuestas', index=False)
            
            # Hoja 3: Fuentes detalladas
            sources_data = []
            for result in self.results:
                for i, source in enumerate(result.get("sources_details", [])):
                    sources_data.append({
                        "test_name": result["test_name"],
                        "query": result["query"],
                        "source_num": i+1,
                        "content_preview": source.get("content_preview", ""),
                        "metadata": source.get("metadata", "")
                    })
            if sources_data:
                pd.DataFrame(sources_data).to_excel(writer, sheet_name='Fuentes', index=False)
            
            # Hoja 4: Métricas agregadas
            metrics = {
                "Métrica": [
                    "Tiempo promedio embedding (ms)",
                    "Tiempo promedio proceso (ms)",
                    "Confianza promedio (%)",
                    "Tasa de éxito RAG (%)",
                    "Documentos promedio encontrados",
                    "Embedding norma promedio"
                ],
                "Valor": [
                    round(df["embedding_time_ms"].mean(), 2),
                    round(df["process_time_ms"].mean(), 2),
                    round(df[df["is_rag_response"]]["confidence_percent"].mean(), 2) if any(df["is_rag_response"]) else 0,
                    round((df["is_rag_response"].sum() / len(df)) * 100, 2),
                    round(df["sources_count"].mean(), 2),
                    round(df["embedding_norm"].mean(), 4)
                ]
            }
            pd.DataFrame(metrics).to_excel(writer, sheet_name='Métricas', index=False)
        
        # Guardar también en JSON para análisis detallado
        json_path = self.debug_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 RESULTADOS GUARDADOS:")
        print(f"   📊 Excel: {excel_path}")
        print(f"   📁 JSON: {json_path}")
        print(f"   📈 Pruebas realizadas: {len(self.results)}")
        
        # Mostrar resumen estadístico
        self._print_statistics(df)
    
    def _print_statistics(self, df: pd.DataFrame):
        """Mostrar estadísticas resumidas"""
        print(f"\n📊 ESTADÍSTICAS DE LA SESIÓN:")
        print(f"   • Pruebas totales: {len(df)}")
        print(f"   • Respuestas RAG: {df['is_rag_response'].sum()} ({df['is_rag_response'].mean()*100:.1f}%)")
        print(f"   • Confianza promedio RAG: {df[df['is_rag_response']]['confidence_percent'].mean():.1f}%")
        print(f"   • Fuentes promedio por consulta: {df['sources_count'].mean():.1f}")
        print(f"   • Tiempo total promedio: {df['total_time_ms'].mean():.1f} ms")
        print(f"   • Embedding norma promedio: {df['embedding_norm'].mean():.3f}")
    
    def compare_with_previous(self, previous_file: str):
        """Comparar con resultados anteriores"""
        try:
            prev_path = self.debug_dir / f"{previous_file}.xlsx"
            if prev_path.exists():
                prev_df = pd.read_excel(prev_path, sheet_name='Resumen')
                current_df = pd.DataFrame([r for r in self.results])
                
                print(f"\n📈 COMPARACIÓN CON {previous_file}:")
                
                # Comparar métricas clave
                metrics = ["total_time_ms", "confidence_percent", "sources_count"]
                for metric in metrics:
                    if metric in prev_df.columns and metric in current_df.columns:
                        prev_mean = prev_df[metric].mean()
                        curr_mean = current_df[metric].mean()
                        change = ((curr_mean - prev_mean) / prev_mean * 100) if prev_mean != 0 else 0
                        
                        arrow = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"
                        print(f"   • {metric}: {prev_mean:.1f} → {curr_mean:.1f} ({change:+.1f}%) {arrow}")
                
                return True
            else:
                print(f"⚠️  Archivo anterior no encontrado: {prev_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error en comparación: {e}")
            return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug avanzado del sistema RAG')
    parser.add_argument('--query', type=str, help='Probar una consulta específica')
    parser.add_argument('--suite', action='store_true', help='Ejecutar suite completa de pruebas')
    parser.add_argument('--compare', type=str, help='Comparar con archivo anterior (sin extensión)')
    parser.add_argument('--name', type=str, default=None, help='Nombre personalizado para el archivo de resultados')
    
    args = parser.parse_args()
    
    # Inicializar debugger
    debugger = RAGDebugger()
    
    # Ejecutar pruebas según argumentos
    if args.query:
        debugger.test_query(args.query, "consulta_personalizada")
    
    if args.suite:
        debugger.run_test_suite()
    
    if not args.query and not args.suite:
        # Ejecutar prueba por defecto
        debugger.test_query("¿Cómo cambio mi correo electrónico?", "prueba_default")
    
    # Guardar resultados
    debugger.save_results(args.name)
    
    # Comparar si se solicita
    if args.compare:
        debugger.compare_with_previous(args.compare)
    
    print(f"\n✅ DEBUG COMPLETADO - {debugger.timestamp}")

if __name__ == "__main__":
    main()