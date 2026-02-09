import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
import logging
from config.settings import settings  # <-- SE AÑADIO ESTA LINEA

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_name: str = None):
        from config.settings import settings
        self.model_name = model_name or settings.EMBEDDING_MODEL
        
        # Modelos optimizados para español y CPU
        if "MiniLM" in self.model_name:
            # Muy ligero y bueno para español
            self.model = SentenceTransformer(self.model_name)
            self.dimension = 384
        else:
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.dimension = 384
            
        logger.info(f"Embedding model loaded: {self.model_name}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Genera embeddings para un texto"""
        return self.model.encode(text, show_progress_bar=False)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Genera embeddings en batch"""
        return self.model.encode(texts, show_progress_bar=False, batch_size=32)