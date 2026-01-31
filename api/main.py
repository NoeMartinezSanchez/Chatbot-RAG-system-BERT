from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uuid
from datetime import datetime

from config.settings import settings
from config.models import ChatRequest, ChatResponse, FeedbackRequest
from rag.core import RAGSystem

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar aplicación
app = FastAPI(title="Asistente Educativo RAG", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar sistema RAG
rag_system = RAGSystem()

# Almacenamiento simple en memoria para feedback
feedback_store = {}
conversation_store = {}

@app.on_event("startup")
async def startup_event():
    """Inicializar sistema al arrancar"""
    try:
        # Cargar intents
        rag_system.load_intents("data/intents.json")
        logger.info("Sistema RAG inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando RAG: {e}")

@app.get("/")
async def root():
    """Endpoint de salud"""
    return {
        "status": "online",
        "service": "Asistente Educativo RAG",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check para Render"""
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal para chat"""
    try:
        # Generar IDs si no existen
        user_id = request.user_id or str(uuid.uuid4())
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Procesar consulta
        response_text, is_rag, confidence, sources = rag_system.process_query(
            request.message
        )
        
        # Crear respuesta
        response = ChatResponse(
            response=response_text,
            sources=sources,
            is_rag_response=is_rag,
            confidence=confidence
        )
        
        # Almacenar conversación
        message_id = str(uuid.uuid4())
        if conversation_id not in conversation_store:
            conversation_store[conversation_id] = []
        
        conversation_store[conversation_id].append({
            "message_id": message_id,
            "user_message": request.message,
            "assistant_response": response_text,
            "timestamp": datetime.now().isoformat(),
            "is_rag": is_rag
        })
        
        # Añadir headers con IDs
        headers = {
            "X-User-ID": user_id,
            "X-Conversation-ID": conversation_id,
            "X-Message-ID": message_id
        }
        
        return JSONResponse(
            content=response.dict(),
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error procesando la consulta")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Endpoint para recibir feedback"""
    try:
        feedback_store[request.message_id] = {
            "conversation_id": request.conversation_id,
            "is_helpful": request.is_helpful,
            "feedback_text": request.feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Feedback recibido: {request.message_id} - Útil: {request.is_helpful}")
        
        return {
            "status": "success",
            "message": "Feedback registrado"
        }
        
    except Exception as e:
        logger.error(f"Error guardando feedback: {e}")
        raise HTTPException(status_code=500, detail="Error guardando feedback")

@app.get("/stats")
async def get_stats():
    """Estadísticas del sistema"""
    return {
        "conversations_count": len(conversation_store),
        "feedback_count": len(feedback_store),
        "system_status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )