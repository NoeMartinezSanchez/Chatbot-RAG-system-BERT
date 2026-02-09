"""
Módulo principal del sistema RAG (Retrieval-Augmented Generation)
"""
import logging
from typing import Tuple, Dict, Any, List
import json
import os
import random

from config.settings import settings
from .embeddings import EmbeddingModel
from .retriever import VectorStoreFAISS
from .generator import ResponseGenerator

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        self.embedder = EmbeddingModel()
        self.vector_store = VectorStoreFAISS()  # <-- CORREGIDO
        self.generator = ResponseGenerator()
        self.intents_loaded = False

        self.top_k = settings.TOP_K_RESULTS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        logger.info("RAG System initialized con FAISS")
    
    def load_intents(self, intents_file: str = "data/vector_store/intents.json"):
        """Carga intents al sistema"""
        try:
            self.vector_store.store_intents(intents_file)
            self.intents_loaded = True
            logger.info("Intents loaded into FAISS vector store")
        except Exception as e:
            logger.error(f"Error loading intents: {e}")
            # Crear archivo básico si no existe
            if not os.path.exists(intents_file):
                basic_intents = {
                    "intents": [
                        {
                            "tag": "saludo",
                            "patterns": ["hola", "buenos días", "buenas tardes"],
                            "responses": ["¡Hola! ¿En qué puedo ayudarte?"],
                            "context": "welcome"
                        }
                    ]
                }
                os.makedirs(os.path.dirname(intents_file), exist_ok=True)
                with open(intents_file, 'w', encoding='utf-8') as f:
                    json.dump(basic_intents, f, ensure_ascii=False, indent=2)
                logger.info("Created basic intents file")
    
    def process_query(self, query: str) -> Tuple[str, bool, float, list]:
        """
        Procesa una consulta y retorna respuesta y metadata
        
        Returns:
            Tuple[str, bool, float, list]: (respuesta, es_rag, confianza, fuentes)
        """
        try:
            # 1. Generar embedding de la consulta
            query_embedding = self.embedder.embed_text(query)
            
            # 2. Primero verificar si es un intent conocido
            if self.intents_loaded:
                intent_results = self.vector_store.search_intents(
                    query_text=query,
                    query_embedding=query_embedding, 
                    top_k=1
                )
                
                # Verificar si hay match de intent
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
                    # Continuar con RAG si hay error
            
            # 3. Buscar documentos relevantes
            doc_results = self.vector_store.search_documents(
                query_embedding, 
                top_k=settings.TOP_K_RESULTS
            )
            
            # Verificar si hay documentos relevantes
            if (not doc_results['documents'] or 
                not doc_results['documents'][0] or
                len(doc_results['documents'][0]) == 0):
                
                # No hay documentos relevantes
                fallback_responses = [
                    "No encontré información específica sobre eso en los materiales. ¿Podrías ser más específico?",
                    "Esa pregunta parece estar fuera del alcance del módulo actual. ¿Hay algo más sobre el módulo en lo que pueda ayudarte?",
                    "No tengo información suficiente para responder eso. Te recomiendo consultar los materiales del módulo directamente."
                ]
                return random.choice(fallback_responses), False, 0.0, []
            
            # 4. Generar respuesta RAG
            contexts = doc_results['documents'][0]
            metadata_list = doc_results['metadatas'][0]
            
            response = self.generator.generate_rag_response(query, contexts)
            
            # 5. Preparar fuentes para mostrar
            sources = []
            for i, (context, metadata) in enumerate(zip(contexts, metadata_list)):
                if i < 2:  # Mostrar máximo 2 fuentes
                    source_info = {
                        "content_preview": context[:100] + "..." if len(context) > 100 else context,
                        "metadata": metadata
                    }
                    sources.append(source_info)
            
            # Calcular confianza basada en distancia (convertir a similitud)
            confidence = 0.0
            if doc_results['distances'] and doc_results['distances'][0]:
                # Convertir distancia L2 a similitud aproximada
                distance = doc_results['distances'][0][0]
                confidence = 1 / (1 + distance) if distance > 0 else 1.0
            
            return response, True, confidence, sources
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Lo siento, tuve un problema procesando tu pregunta. ¿Podrías intentarlo de nuevo?", False, 0.0, []
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None):
        """Añade un documento al sistema"""
        if metadata is None:
            metadata = {}
        
        try:
            # Generar embedding
            embedding = self.embedder.embed_text(content)
            
            # Añadir al vector store
            self.vector_store.add_document(content, metadata, embedding)
            
            logger.info(f"Document added: {metadata.get('title', 'No title')}")
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
    
    def add_documents_batch(self, documents: List[Dict[str, Any]]):
        """Añade múltiples documentos en lote"""
        if not documents:
            return
        
        try:
            # Extraer textos
            texts = [doc['content'] for doc in documents]
            
            # Generar embeddings en batch
            embeddings = self.embedder.embed_batch(texts)
            
            # Añadir al vector store
            self.vector_store.add_documents(documents, embeddings)
            
            logger.info(f"Added {len(documents)} documents in batch")
            
        except Exception as e:
            logger.error(f"Error adding documents batch: {e}")
    
    def get_stats(self):
        """Obtener estadísticas del sistema"""
        try:
            return {
                "vector_store": self.vector_store.get_stats(),
                "embedding_model": self.embedder.model_name,
                "intents_loaded": self.intents_loaded
            }
        except:
            return {"status": "unknown"}