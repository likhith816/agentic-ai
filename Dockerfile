FROM python:3.11-slim

# Install ALL system dependencies needed for the packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    libsndfile1 \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create all necessary runtime directories
RUN mkdir -p \
    uploads/images \
    uploads/csv \
    uploads/audio \
    uploads/audio_responses \
    uploads/documents \
    reports \
    src/knowledge_base/faiss_index \
    src/knowledge_base/documents \
    src/models \
    src/data

# Expose default port
EXPOSE 8000

# Use sh -c so ${PORT} env var expands correctly at runtime
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
