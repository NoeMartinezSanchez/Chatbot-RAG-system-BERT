#!/usr/bin/env python3
"""
Debugger simplificado para chunks PDF
Genera el mismo formato que el debug original pero para documentos PDF
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PDFChunkDebuggerSimple:
    """Debugger simplificado para evaluar chunks de PDF"""
    
    def __init__(self):
        from rag.core import RAGSystem
        from rag.embeddings import EmbeddingModel
        
        self.rag = RAGSystem()
        self.embedder = EmbeddingModel()
        self.results = []
        self.debug_dir = Path("debug")
        self.debug_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🔍 DEBUGGER PDF SIMPLIFICADO - {self.timestamp}")
        print("=" * 70)
    
    def test_query(self, query: str, test_name: str = "pdf_test"):
        """
        Probar una consulta específica
        - query: la pregunta a evaluar
        - test_name: nombre identificador para la prueba
        """
        
        print(f"\n🧪 PRUEBA: '{test_name}'")
        print(f"📝 Consulta: {query}")
        print("-" * 50)

        start_time = time.time()

        # Embedding
        embedding_start = time.time()
        embedding = self.embedder.embed_text(query)
        embedding_time = time.time() - embedding_start
    
        # Procesar consulta
        process_start = time.time()
        response, is_rag, confidence, sources = self.rag.process_query(query)
        process_time = time.time() - process_start
    
        # Estadísticas del sistema
        stats = self.rag.get_stats()

        # Métricas del embedding
        if embedding is not None and len(embedding) > 0:
            embedding_norm = float(np.linalg.norm(embedding))
            embedding_mean = float(np.mean(embedding))
            embedding_std = float(np.std(embedding))
        else:
            embedding_norm = embedding_mean = embedding_std = 0.0
    
        # Detalles de búsqueda (ahora incluye textos completos)
        search_details = self._get_search_details(query, embedding)
    
        # Obtener textos completos de las fuentes
        textos_completos = []
        chunks_ids = []

        for i, source in enumerate(sources[:3]):  # Solo top 3
            texto_completo = source.get("content", "")
            if not texto_completo:
                texto_completo = source.get("content_preview", "")
        
            chunk_id = source.get("metadata", {}).get("chunk_id", "N/A")
        
            textos_completos.append(f"=== DOCUMENTO {i+1} (Chunk: {chunk_id}) ===\n{texto_completo}")
            chunks_ids.append(chunk_id)
    
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "query": query,
            "embedding_time_ms": round(embedding_time * 1000, 2),
            "process_time_ms": round(process_time * 1000, 2),
            "total_time_ms": round((time.time() - start_time) * 1000, 2),
            "is_rag_response": is_rag,
            "confidence_percent": round(confidence * 100, 2),
            "sources_count": len(sources),
            "embedding_norm": round(embedding_norm, 4),
            "embedding_mean": round(embedding_mean, 4),
            "embedding_std": round(embedding_std, 4),
            "total_documents": stats.get("vector_store", {}).get("total_documents", 0),
            "response_completa": response,  # Respuesta completa sin truncar
            "textos_completos": "\n\n".join(textos_completos),  # Textos completos de los 5 docs
            "chunks_ids": ", ".join(chunks_ids),  # IDs de los chunks
            "best_similarity": search_details.get("best_similarity", 0),
            "documents_found": search_details.get("documents_found", 0)
        }

        self.results.append(result)
        self._print_result(result)
        return result
    
    def _get_search_details(self, query: str, query_embedding: np.ndarray) -> Dict:
        """Obtener detalles de la búsqueda"""
        try:
            vector_store = self.rag.vector_store
            
            if hasattr(vector_store, 'search_documents'):
                results = vector_store.search_documents(query_embedding, top_k=3)
                
                if results.get('distances') and results['distances'][0]:
                    distances = results['distances'][0]
                    similarities = [1/(1+d) if d>0 else 1.0 for d in distances]
                    
                    return {
                        "best_similarity": round(max(similarities)*100, 2) if similarities else 0,
                        "documents_found": len(results.get('documents', [[]])[0])
                    }
        except Exception as e:
            logger.warning(f"No se pudieron obtener detalles de búsqueda: {e}")
        
        return {"best_similarity": 0, "documents_found": 0}
    
    def _print_result(self, result: Dict):
        """Mostrar resultado en terminal"""
        print(f"⏱️ TIEMPOS:")
        print(f"   • Embedding: {result['embedding_time_ms']} ms")
        print(f"   • Proceso: {result['process_time_ms']} ms")
        print(f"   • Total: {result['total_time_ms']} ms")
    
        print(f"\n🎯 RESULTADO:")
        print(f"   • ¿Es RAG?: {'✅ SÍ' if result['is_rag_response'] else '❌ NO'}")
        print(f"   • Confianza: {result['confidence_percent']}%")
        print(f"   • Fuentes encontradas: {result['sources_count']}")
        print(f"   • Mejor similitud: {result['best_similarity']}%")
        print(f"   • Chunks IDs: {result['chunks_ids']}")
    
        print(f"\n📝 RESPUESTA COMPLETA:")
        print(f"   {result['response_completa']}")
    
        print(f"\n📚 PRIMER DOCUMENTO RECUPERADO (muestra):")
        primeros_200 = result['textos_completos'][:200] + "..." if len(result['textos_completos']) > 200 else result['textos_completos']
        print(f"   {primeros_200}")
    
        print("\n" + "=" * 70)
    
    def save_results(self, filename: str = None):
        """Guardar resultados en Excel"""
        if not self.results:
            print("❌ No hay resultados para guardar")
            return
    
        if filename is None:
            filename = f"pdf_debug_{self.timestamp}"
    
        excel_path = self.debug_dir / f"{filename}.xlsx"
    
        # Crear DataFrame
        df = pd.DataFrame(self.results)
    
        # Columnas actualizadas
        column_order = [
            "timestamp", "test_name", "query", 
            "embedding_time_ms", "process_time_ms", "total_time_ms",
            "is_rag_response", "confidence_percent", "sources_count",
            "embedding_norm", "embedding_mean", "embedding_std",
            "total_documents", "response_completa", "textos_completos",
            "chunks_ids", "best_similarity", "documents_found"
        ]
    
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
    
        # Guardar Excel (puede ser grande por los textos completos)
        df.to_excel(excel_path, index=False)
    
        print(f"\n💾 RESULTADOS GUARDADOS:")
        print(f"   📊 Excel: {excel_path}")
        print(f"   📈 Pruebas realizadas: {len(self.results)}")
    
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   • Respuestas RAG: {df['is_rag_response'].sum()}/{len(df)} ({df['is_rag_response'].mean()*100:.1f}%)")
        print(f"   • Confianza promedio: {df['confidence_percent'].mean():.1f}%")
        print(f"   • Tiempo promedio: {df['total_time_ms'].mean():.1f} ms")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debugger simplificado para chunks PDF')
    parser.add_argument('--name', type=str, default=None, 
                       help='Nombre personalizado para el archivo de resultados')
    
    args = parser.parse_args()
    
    debugger = PDFChunkDebuggerSimple()
    
    # ============================================================
    # AQUÍ COLOCA TUS PREGUNTAS - EJEMPLOS
    # ============================================================
    # Formato:
    # debugger.test_query("tu pregunta aquí", "nombre_identificador")
    # ============================================================
    
    # === EJEMPLOS (reemplázalos con tus preguntas) ===

    
    # ============================================================
    # BASES CONVOCATORIA
    # ============================================================
    
    debugger.test_query(
        "¿Cuál es la fecha límite absoluta para registrarme?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Qué características deben tener mis correos electrónicos?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Qué pasa si solo subo una foto de mi acta de nacimiento con el celular?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Puedo usar mi INE como comprobante de domicilio?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Mi equipo actual cumple con los requisitos técnicos?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Cuánto tiempo me tomará terminar la prepa?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Cómo se estructura cada módulo?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Qué consecuencia tiene subir un documento falso?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Puedo pedirle a alguien más que haga mi registro?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Qué pasa si aún no tengo mi certificado de secundaria porque me acabo de terminar?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Es opcional el módulo propedéutico?",
        "bases_convocatoria"
        )

    debugger.test_query(
        "¿Cuándo y cómo obtengo mis claves de acceso?",
        "bases_convocatoria"
        )

    # ============================================================
    # CONSTRUYENDO COMUNIDAD
    # ============================================================
    
    debugger.test_query(
        "Si un compañero publica algo con lo que no estoy de acuerdo, ¿cómo debo responderle según el decálogo?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿Por qué es importante cuidar mi lenguaje digital si solo estamos escribiendo en un foro?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿Qué significa respetar los tiempos de atención en una modalidad que es flexible?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "Si noto que un compañero está desanimado o le cuesta un tema, ¿qué principio del decálogo puedo aplicar?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿Qué debo hacer si presencio un acto de falta de respeto o violencia en la plataforma?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿Por qué el decálogo menciona los Derechos Humanos en una regla de comunicación?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿Cómo puedo aplicar la actitud abierta al aprendizaje cuando me dan una retroalimentación negativa en una tarea?",
        "construyendo_comunidad"
        )

    debugger.test_query(
        "¿A qué se refiere el texto con evitar prejuicios y estereotipos en mis tareas o participaciones?",
        "construyendo_comunidad"
        )

    # ============================================================
    # GUIA ASPIRANTE
    # ============================================================
    
    debugger.test_query(
        "¿Qué pasa si me equivoco en una letra de mi correo electrónico al registrarme?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Las respuestas del cuestionario afectan mi calificación o mis posibilidades de entrar?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Puedo empezar el cuestionario hoy y terminarlo mañana?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Puedo usar una aplicación del celular para escanear mis documentos?",
        "guia_aspirante"
        )

    debugger.test_query(
        "Mi certificado de secundaria no tiene nada atrás, ¿dejo ese espacio en blanco?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Es verdad que el propedéutico dura solo 10 días?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Qué calificación necesito para asegurar mi inscripción al Módulo 1?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Cuándo me dan mi correo institucional y mi matrícula oficial?",
        "guia_aspirante"
        )

    debugger.test_query(
        "Si pierdo mi contraseña del aula, ¿con quién me comunico?",
        "guia_aspirante"
        )

    debugger.test_query(
        "¿Puedo entrar a la plataforma a las 3 de la mañana si trabajo todo el día?",
        "guia_aspirante"
        )

    debugger.test_query(
        "Si ya cursé un año de prepa en otra escuela, ¿tengo que empezar desde el Módulo 1?",
        "guia_aspirante"
        )

    # ============================================================
    # NORMAS CONTROL ESCOLAR
    # ============================================================
    
    debugger.test_query(
        "¿Cuál es la calificación mínima necesaria para acreditar un módulo en Prepa en Línea-SEP?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "Si un estudiante acumula un total de 4 módulos no acreditados, ¿cuál es la consecuencia según las normas?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "¿Cuánto tiempo dura el periodo de recuperación para aquellos que no aprobaron en el periodo ordinario?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "¿Cuál es el plazo máximo improrrogable que tiene un estudiante para terminar sus estudios?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "En caso de ausencia del Facilitador (Asesor Virtual), ¿quién es el responsable de evaluar las actividades?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "¿Qué documento es indispensable para que la inscripción pase de 'provisional' a 'definitiva'?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "¿Cuál es el tiempo máximo que un Facilitador tiene para evaluar una actividad después de que se sube a la plataforma?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "Si un estudiante decide solicitar una baja temporal, ¿cuál es el periodo máximo que puede durar?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "¿En qué formato se emiten los certificados de terminación de estudios en Prepa en Línea-SEP?",
        "normas_control_escolar"
        )

    debugger.test_query(
        "Si un estudiante irregular tiene una calificación de entre 50 y 59 en un módulo, ¿qué proceso de regularización le corresponde?",
        "normas_control_escolar"
        )


    # ============================================================
    # PRONUNCIAMIENTO CERO TOLERANCIA
    # ============================================================
    
    debugger.test_query(
        "Oye, subí mi Proyecto Integrador el viernes a las 11 de la noche... ¿Para cuándo ya debería estar calificado según el reglamento?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "¿Cuál es la calificación mínima que ocupo para no irme a recuperación y pasar limpio el módulo?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Ando bien atrasado... ¿Cuántos módulos puedo dejar sin acreditar antes de que me den de baja definitiva y pierda mi matrícula?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Se me ha complicado la chamba y he pedido bajas temporales... ¿Cuánto es lo máximo que tengo de chance para terminar toda la prepa?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "No alcancé a pasar el módulo ordinario, ¿cuántos días me dan para recuperarme y quién me califica si mi asesor ya no está?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Entré con inscripción provisional porque no encontraba mi certificado de secundaria, ¿cuánto tiempo me dieron de prórroga antes de que me corten el acceso a la plataforma?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Saqué 52 final en el módulo. ¿Me toca volver a cursar todo el mes (recursamiento) o solo hacer una actividad extra (remedial)?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Me voy a ir a trabajar a un lugar sin internet un tiempo, ¿cuánto es lo máximo que puedo pedir de baja temporal sin que me saquen?",
        "pronunciamiento_cero_tolerancia"
        )

    debugger.test_query(
        "Cuando por fin termine los 23 módulos, ¿tengo que ir a las oficinas de la SEP en CDMX para que me sellen el certificado?",
        "pronunciamiento_cero_tolerancia"
        )

    # ============================================================
    # PROTOCOLO CONVIVENCIA
    # ============================================================
    
    debugger.test_query(
        "Oye, si un compañero empieza a publicar capturas de pantalla de mis tareas en un grupo de Facebook para burlarse de mí o me manda mensajes ofensivos por Messenger, ¿la Prepa puede hacer algo aunque no sea dentro de la plataforma oficial?",
        "protocolo_convivencia"
        )

    debugger.test_query(
        "En mi grupo de WhatsApp hay mucha gente de diferentes estados y a veces hay comentarios pesados sobre cómo hablamos o nuestras creencias. ¿Eso se considera discriminación según el protocolo?",
        "protocolo_convivencia"
        )

    debugger.test_query(
        "¿Qué pasa si siento que una figura escolar (como un asesor o tutor) me está presionando de forma inadecuada o usa lenguaje que me hace sentir incómodo de forma constante?",
        "protocolo_convivencia"
        )

    debugger.test_query(
        "Si yo me entero de que a una compañera la están acosando en el foro de dudas, pero a mí no me están haciendo nada, ¿tengo que decir algo?",
        "protocolo_convivencia"
        )

    debugger.test_query(
        "¿A qué se refiere la Prepa cuando dice que debemos tener una 'Cultura de Paz' en los foros?",
        "protocolo_convivencia"
        )

    debugger.test_query(
        "¿Estas reglas solo aplican cuando estoy conectado en la plataforma haciendo mis actividades?",
        "protocolo_convivencia"
        )

    # ============================================================
    # REGLAS COMUNICACION
    # ============================================================
    
    debugger.test_query(
        "¿Qué son las reglas de comuncación?",
        "reglas_comunicacion"
        )

    debugger.test_query(
        "¿Qué lenguaje tenemos que emplear?",
        "reglas_comunicacion"
        )

    debugger.test_query(
        "¿No entindo lo que me dicen?",
        "reglas_comunicacion"
        )


    # ============================================================
    
    # Guardar resultados
    debugger.save_results(args.name)
    
    print(f"\n✅ DEBUG COMPLETADO - {debugger.timestamp}")

if __name__ == "__main__":
    main()