# QueryPilot backend for Railway. HuggingFace or OpenAI embeddings; no ragas.
# EMBEDDING_PROVIDER=huggingface (default) or openai.
FROM python:3.12-slim

WORKDIR /app

# CPU-only PyTorch first so sentence-transformers doesn't pull CUDA (smaller image)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# App deps (includes sentence-transformers for HuggingFace embeddings)
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# App code
COPY . .

# Railway sets PORT
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
