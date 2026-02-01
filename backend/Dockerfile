# QueryPilot backend - minimal image for Railway (no torch/ragas).
# Set EMBEDDING_PROVIDER=openai and OPENAI_API_KEY.
FROM python:3.12-slim

WORKDIR /app

# Install deps first (better layer cache)
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# App code
COPY . .

# Railway sets PORT
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
