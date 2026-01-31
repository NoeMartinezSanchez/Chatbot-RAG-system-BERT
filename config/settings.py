import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    LLM_MODEL: str = "hackathon-somos-nlp-2023/BSC-LT-Project/roberta-base-bne-capitel-ner-plus"
    
    # RAG Configuration
    CHUNK_SIZE: int = 768
    CHUNK_OVERLAP: int = 128
    TOP_K_RESULTS: int = 3
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Vector Database (local first, then AWS compatible)
    VECTOR_STORE: str = "chroma"  # or "faiss" for production
    PERSIST_DIRECTORY: str = "./data/vector_store"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # AWS Configuration (for future migration)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    
    class Config:
        env_file = ".env"

    # FAISS Configuration
    FAISS_INDEX_TYPE: str = "FlatL2"  # "FlatL2", "IVFFlat", etc.
    FAISS_METRIC: str = "cosine"      # "cosine", "l2", "ip"
    FAISS_EMBEDDING_DIM: int = 384    # Dimensión de MiniLM
    
    # Persistencia
    FAISS_PERSIST_DIR: str = "./data/vector_store"
    
    # Búsqueda
    FAISS_SEARCH_K: int = 3           # Resultados por búsqueda
    FAISS_SIMILARITY_THRESHOLD: float = 0.7

settings = Settings()