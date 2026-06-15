FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core deps first (faster layer caching)
COPY requirements.txt .

# Install in stages to isolate failures
RUN pip install --no-cache-dir fastapi==0.110.0 uvicorn[standard]==0.29.0 python-multipart==0.0.9 python-dotenv==1.0.1 pydantic==2.7.0
RUN pip install --no-cache-dir groq==0.9.0 google-generativeai==0.7.2
RUN pip install --no-cache-dir langgraph==0.2.28 langchain==0.2.16 langchain-community==0.2.16 langchain-text-splitters==0.2.4
RUN pip install --no-cache-dir pypdf==4.3.1 fpdf2==2.7.9 gTTS==2.5.1 soundfile==0.12.1 httpx==0.27.0 aiofiles==23.2.1
RUN pip install --no-cache-dir numpy==1.26.4 pandas==2.2.2 scikit-learn==1.5.0 joblib==1.4.2
RUN pip install --no-cache-dir xgboost==2.1.1 || echo "xgboost install failed - continuing"
RUN pip install --no-cache-dir faiss-cpu==1.8.0 || pip install --no-cache-dir faiss-cpu || echo "faiss-cpu install failed - continuing"

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p \
    uploads/images uploads/csv uploads/audio uploads/audio_responses \
    uploads/documents reports \
    src/knowledge_base/faiss_index src/knowledge_base/documents \
    src/models src/data

EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
