# Zx Lens backend — production container for Render / any Docker host
FROM python:3.12-slim

# Non-interactive, deterministic builds
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Native libs needed by torch/sentence-transformers/docling wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (caches layers; rebuilds are fast)
COPY backend/requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the whole backend so relative data paths (backend/data/...) resolve from /app
COPY backend/ backend/

# Ensure storage dirs exist and are writable
RUN mkdir -p \
        backend/data/raw \
        backend/data/processed \
        backend/data/indices/chroma \
        backend/data/indices/bm25

EXPOSE 10000

# Render injects a PORT env var; fall back to 10000 locally.
CMD ["sh", "-c", "uvicorn backend.src.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
