# rag/generator.py - VERSIÓN CORREGIDA
from typing import List, Dict, Any
import random
import logging
import time

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self):
        self.use_advanced_qa = False
        self.qa_pipeline = None
        
        # Intentar cargar modelo avanzado solo si torch >= 2.6
        try:
            import torch
            torch_version = torch.__version__.split('.')
            major, minor = int(torch_version[0]), int(torch_version[1])
            
            if major >= 2 and minor >= 6:
                logger.info(f"Torch {torch.__version__} >= 2.6, intentando cargar QA pipeline")
                self._try_load_qa_pipeline()
            else:
                logger.warning(f"Torch {torch.__version__} < 2.6, usando modo simple")
                self.use_advanced_qa = False
                
        except Exception as e:
            logger.warning(f"No se pudo verificar torch versión: {e}")
            self.use_advanced_qa = False
        
        logger.info(f"ResponseGenerator inicializado. Modo QA: {self.use_advanced_qa}")
    
    def _try_load_qa_pipeline(self):
        """Intentar cargar pipeline de QA"""
        try:
            from transformers import pipeline
            
            # Modelo ligero para español
            model_name = "mrm8488/bert-tiny-5-finetuned-squadv2"
            
            self.qa_pipeline = pipeline(
                "question-answering",
                model=model_name,
                tokenizer=model_name,
                device=-1,  # CPU
                max_answer_len=150,
                handle_impossible_answer=True
            )
            
            self.use_advanced_qa = True
            logger.info(f"QA pipeline cargado: {model_name}")
            
        except Exception as e:
            logger.warning(f"No se pudo cargar QA pipeline: {e}")
            self.use_advanced_qa = False
            self.qa_pipeline = None
    
    def generate_from_intent(self, intent_data: Dict[str, Any]) -> str:
        """Genera respuesta desde un intent"""
        responses = intent_data.get('responses', [])
        if responses:
            return random.choice(responses)
        return "¿En qué más puedo ayudarte?"
    
    def generate_rag_response(self, query: str, contexts: List[str]) -> str:
        """Genera respuesta usando RAG"""
        if not contexts:
            return "No encontré información específica sobre eso en los materiales."
        
        # Si tenemos QA pipeline y queremos usarlo
        if self.use_advanced_qa and self.qa_pipeline:
            try:
                return self._generate_with_qa(query, contexts)
            except Exception as e:
                logger.warning(f"QA falló, usando modo simple: {e}")
        
        # Modo simple (fallback)
        return self._generate_simple(query, contexts)
    
    def _generate_with_qa(self, query: str, contexts: List[str]) -> str:
        """Generar respuesta con modelo de QA - CORREGIDO"""
        # Combinar contextos
        combined_context = "\n\n".join(contexts[:2])  # Usar máximo 2
        
        try:
            result = self.qa_pipeline(
                question=query,
                context=combined_context,
                max_answer_len=200
            )
            
            # IMPORTANTE: Verificar si la respuesta es válida
            answer_text = result['answer'].strip()
            confidence = result['score']
            
            logger.info(f"QA result - Answer: '{answer_text}', Confidence: {confidence:.3f}")
            
            # Filtrar respuestas no válidas
            invalid_responses = ['.', '', ' ', '..', '...', ',', ';', ':', '-', '–']
            
            if (confidence > 0.3 and 
                answer_text and 
                answer_text not in invalid_responses and
                len(answer_text) > 10):  # Al menos 10 caracteres
                
                # Formatear respuesta
                if not answer_text.endswith('.'):
                    answer_text = answer_text + '.'
                
                # Añadir nota de fuente solo si es relevante
                formatted = f"{answer_text}\n\n💡 *Información basada en materiales del módulo*"
                
                return formatted
            else:
                # Confianza baja o respuesta inválida, usar modo simple
                logger.info(f"Respuesta QA rechazada (confianza: {confidence:.3f}, texto: '{answer_text}')")
                return self._generate_simple(query, contexts)
                
        except Exception as e:
            logger.error(f"Error en QA: {e}")
            return self._generate_simple(query, contexts)
    
    def _generate_simple(self, query: str, contexts: List[str]) -> str:
        """Generar respuesta simple (fallback) - MEJORADO"""
        if not contexts:
            return "No tengo información específica sobre ese tema en los materiales del módulo."
        
        best_context = contexts[0]
        
        # Filtrar contexto demasiado corto
        if len(best_context.strip()) < 20:
            if len(contexts) > 1:
                best_context = contexts[1]
            else:
                return "Encontré información pero no es suficientemente relevante para tu pregunta."
        
        # Analizar la pregunta para dar mejor contexto
        question_lower = query.lower()
        
        # Determinar tipo de pregunta
        if any(word in question_lower for word in ["qué", "qué es", "qué son", "defin", "concepto", "significa"]):
            # Pregunta de definición
            response = "Según los materiales del módulo:\n\n"
        elif any(word in question_lower for word in ["cómo", "cómo se", "procedimiento", "pasos", "metodología"]):
            # Pregunta de procedimiento
            response = "El procedimiento descrito en los materiales es:\n\n"
        elif any(word in question_lower for word in ["cuánto", "cuántos", "cuántas", "duración", "tiempo", "fecha"]):
            # Pregunta cuantitativa
            response = "En relación a tu consulta sobre cantidades o tiempos:\n\n"
        else:
            # Pregunta general
            response = "Encontramos esta información relevante en los materiales:\n\n"
        
        # Extraer las oraciones más relevantes (mejorado)
        sentences = best_context.split('. ')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # Filtrar oraciones muy cortas
        
        if not sentences:
            # Si no hay oraciones válidas, usar el contexto completo
            sentences = [best_context]
        
        # Tomar 1-2 oraciones más relevantes
        max_sentences = min(2, len(sentences))
        selected_sentences = sentences[:max_sentences]
        
        # Formatear
        response += '. '.join(selected_sentences)
        if not response.endswith('.'):
            response += '.'
        
        # Pregunta de seguimiento personalizada
        if "matemáticas" in question_lower or "matematica" in question_lower:
            follow_up = "\n\n¿Necesitas ayuda con algún ejercicio específico de matemáticas?"
        elif "física" in question_lower or "fisica" in question_lower:
            follow_up = "\n\n¿Te gustaría profundizar en algún concepto de física?"
        elif "química" in question_lower or "quimica" in question_lower:
            follow_up = "\n\n¿Hay algún tema de química en el que necesites más ayuda?"
        else:
            follow_up_options = [
                "\n\n¿Esta información responde a tu pregunta?",
                "\n\n¿Necesitas más detalles sobre este tema?",
                "\n\n¿Hay algún aspecto específico que te gustaría que amplíe?"
            ]
            follow_up = random.choice(follow_up_options)
        
        response += follow_up
        
        return response
    
    def generate_fallback_response(self, query: str) -> str:
        """Generar respuesta de fallback cuando no hay información relevante"""
        fallbacks = [
            f"No encontré información específica sobre '{query}' en los materiales del módulo. Mis conocimientos están enfocados en el contenido del módulo propedéutico.",
            f"Esa pregunta parece estar fuera del alcance de mis materiales actuales. ¿Hay algo relacionado con el módulo propedéutico en lo que pueda ayudarte?",
            f"Actualmente no tengo información suficiente sobre ese tema. Te recomiendo consultar los materiales oficiales del módulo o preguntar a tu tutor.",
            f"Mis conocimientos se centran en el módulo propedéutico. ¿Podrías reformular tu pregunta para que esté relacionada con el contenido del módulo?"
        ]
        
        return random.choice(fallbacks)