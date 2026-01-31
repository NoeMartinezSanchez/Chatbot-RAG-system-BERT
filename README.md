# 🤖 Chatbot RAG para Prepa en Línea SEP

Sistema de asistencia educativa inteligente con Retrieval-Augmented Generation (RAG) diseñado para proporcionar soporte 24/7 a 16,000 estudiantes mensuales de la plataforma Prepa en Línea SEP.

[![Python](https://img.shields.io/badge/Python-3.12.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [API](#-api)
- [Métricas de Performance](#-métricas-de-performance)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías](#-tecnologías)
- [Roadmap](#-roadmap)
- [Contribuciones](#-contribuciones)
- [Autores](#-autores)

## 🎯 Descripción

Este proyecto implementa un chatbot educativo basado en RAG que combina:

- **Reconocimiento de intenciones (Intents)** para respuestas predefinidas
- **Búsqueda semántica (RAG)** sobre base de conocimientos institucional
- **Procesamiento de tickets históricos** de la Mesa de Servicio

El sistema procesa documentación institucional y más de 500 tickets categorizados para proporcionar respuestas contextualizadas y precisas a las consultas de los estudiantes.

## ✨ Características

- ✅ **RAG Pipeline completo** con integración BERT
- ✅ **Embeddings multilingües** usando Sentence Transformers
- ✅ **Base de datos vectorial** FAISS optimizada para producción
- ✅ **API REST** documentada con FastAPI
- ✅ **Ingesta automatizada** de documentos Excel
- ✅ **30+ casos reales** integrados de la mesa de servicio
- 🔄 **Respuesta híbrida** combinando intents y RAG
- 🔄 **Pipeline de procesamiento** con chunking inteligente

## 🏗️ Arquitectura

```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         API REST (FastAPI)          │
└──────┬──────────────────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌─────────────────┐
│ Intent       │   │  RAG Pipeline   │
│ Recognition  │   │                 │
└──────────────┘   └────┬────────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌─────────────┐    ┌─────────────┐
       │  Embeddings │    │    FAISS    │
       │  (MiniLM)   │    │  VectorDB   │
       └─────────────┘    └─────────────┘
```

### Componentes principales

- **Backend**: FastAPI 0.104.1 + Python 3.12.10
- **Modelos de ML**:
  - Embeddings: `paraphrase-multilingual-MiniLM-L12-v2`
  - NLP: `roberta-base-bne-capitel-ner-plus`
- **Base de datos vectorial**: FAISS CPU 1.13.2 con índice FlatL2 (384 dimensiones)
- **Pipeline de datos**: Ingesta automatizada con chunking inteligente (768/128)

## 🚀 Instalación

### Requisitos previos

- Python 3.12+
- pip o conda
- 2GB+ RAM disponible

### Configuración del entorno

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/chatbot-prepa-linea-sep.git
cd chatbot-prepa-linea-sep

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias principales

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sentence-transformers==2.2.2
torch==2.9.1
transformers==4.41.2
faiss-cpu==1.13.2
tiktoken==0.7.0
numpy==1.26.4
```

## 💻 Uso

### Iniciar el servidor local

```bash
# Configurar variables de entorno
export ENVIRONMENT=development

# Ejecutar servidor
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Procesar documentos

```bash
# Ingestar documentos Excel a FAISS
python scripts/upload_documents.py --file data/documents/tickets.xlsx
```

### Realizar consultas

```python
import requests

# Consulta directa al chatbot
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "¿Cómo recupero mi número de folio?"}
)

print(response.json())
```

## 📡 API

### Endpoints principales

#### `POST /chat`

Envía una consulta al chatbot.

**Request:**
```json
{
  "message": "hola, tengo una duda sobre el módulo"
}
```

**Response:**
```json
{
  "response": "¡Hola! 👋 Soy tu asistente especializado...",
  "is_rag_response": false,
  "confidence": 0.9,
  "sources": []
}
```

#### `POST /ingest`

Ingesta nuevos documentos a la base de conocimientos.

**Documentación interactiva**: `http://localhost:8000/docs`

## 📊 Métricas de Performance

| Métrica | Valor Actual | Objetivo | Estado |
|---------|--------------|----------|--------|
| Tiempo de Respuesta | 1.2 seg | < 2 seg | ✅ |
| Precisión de Intents | 85% | > 90% | 🟡 |
| Recall en Tickets | 78% | > 85% | 🟡 |
| Uso de Memoria | 1.8 GB | < 2 GB | ✅ |
| Throughput API | 10 req/seg | 50+ req/seg | 🔄 |

## 📁 Estructura del Proyecto

```
chatbot-prepa-linea-sep/
├── api/                    # API REST con FastAPI
│   ├── endpoints.py        # Endpoints principales
│   └── main.py            # Configuración API
├── config/                # Configuración centralizada
│   ├── settings.py        # Variables de entorno
│   └── models.py          # Modelos Pydantic
├── rag/                   # Núcleo RAG
│   ├── retriever.py       # Búsqueda FAISS
│   ├── embeddings.py      # Modelo multilingüe
│   ├── generator.py       # Generación respuestas
│   └── core.py            # Orquestación principal
├── data/                  # Datos y almacenamiento
│   ├── documents/         # Documentos fuente
│   ├── vector_store/      # Índices FAISS
│   └── intents.json       # Base de intenciones
├── scripts/               # Utilidades
│   ├── upload_documents.py # Pipeline Excel → FAISS
│   └── setup_local.py     # Configuración local
└── docker/                # Configuración contenedores
```

## 🛠️ Tecnologías

- **Framework Web**: FastAPI
- **ML/NLP**: 
  - Sentence Transformers (embeddings multilingües)
  - Hugging Face Transformers
  - PyTorch
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Procesamiento**: tiktoken, numpy, pandas
- **Deployment**: Docker, Render (planificado)

### Configuración óptima

```python
OPTIMAL_CONFIG = {
    "chunk_size": 768,           # Balance contexto/performance
    "chunk_overlap": 128,        # Mantener continuidad
    "top_k_results": 3,          # Respuestas balanceadas
    "similarity_threshold": 0.7, # Filtro calidad
    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

## 🗺️ Roadmap

### ✅ Completado
- [x] Implementación completa del pipeline RAG
- [x] Sistema de embeddings multilingüe
- [x] Base de datos vectorial FAISS optimizada
- [x] API REST operativa
- [x] Pipeline de ingesta automatizada
- [x] Integración de 30 casos reales

### 🔄 En Progreso
- [ ] Dockerización del proyecto
- [ ] Despliegue en Render
- [ ] Optimización de performance para alto volumen

### 📋 Próximos Pasos
- [ ] Mejora del modelo de reconocimiento de intents (objetivo: >90% precisión)
- [ ] Integración completa base de conocimientos (500+ tickets - 10 Feb)
- [ ] Sistema de pruebas automatizadas
- [ ] Documentación pipeline de ingesta de tickets
- [ ] Métricas avanzadas de monitoreo
- [ ] Interfaz de usuario para pruebas

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 👥 Autores

- **Erick Delgadillo** - Desarrollo e Implementación
- **Noé Martinez** - Desarrollo e Implementación

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

Para preguntas o soporte relacionado con el proyecto de Prepa en Línea SEP, contacta al equipo de desarrollo.

---

**Última actualización**: Enero 29, 2026

**Estado del proyecto**: 🟢 En desarrollo activo