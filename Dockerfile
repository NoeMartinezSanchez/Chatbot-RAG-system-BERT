# Usar imagen oficial de Python 3.11
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorios necesarios
RUN mkdir -p data/vector_store data/documents logs

# Exponer puerto (Render asignará automáticamente)
EXPOSE 8000

# Comando de inicio - usa el puerto que Render asigna
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT