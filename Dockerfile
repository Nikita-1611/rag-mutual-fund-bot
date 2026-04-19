# Use a slim Python image for minimal footprint
FROM python:3.11-slim

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install production requirements
# fastembed replaces sentence-transformers/torch, saving ~300MB RAM
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model into the image cache
# This ensures startup is fast and won't exceed RAM during runtime download
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

# Copy the backend source code
# .dockerignore ensures that frontend/, output/, etc. are NOT copied
COPY src/ ./src/

# Expose the API port (Render sets $PORT env var)
EXPOSE 10000

# Start command: Use 1 worker to keep memory usage low on Render Free Tier (512MB RAM)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
