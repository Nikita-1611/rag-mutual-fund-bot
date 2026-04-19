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

# Install CPU-only torch to drastically reduce image size and memory footprint
# This prevents downloading ~1GB of CUDA binaries which are useless on Render Free Tier
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model to ensure fast startup and prevent runtime downloads
# This saves the model into the image during the build process
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Copy the backend source code
# Note: .dockerignore ensures that frontend/, output/, etc. are NOT copied
COPY src/ ./src/

# Expose the API port (Render sets $PORT env var)
EXPOSE 10000

# Start command: Use 1 worker to keep memory usage low on Render Free Tier (512MB RAM)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
