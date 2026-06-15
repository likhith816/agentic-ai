FROM python:3.11-slim

# System deps needed for faiss-cpu, soundfile, xgboost
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads/images uploads/csv uploads/audio uploads/documents reports \
    src/knowledge_base/faiss_index src/knowledge_base/documents \
    src/models src/data

# Expose default port (Railway overrides via $PORT)
EXPOSE 8000

# Use sh -c so ${PORT} env var expands correctly at runtime
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
