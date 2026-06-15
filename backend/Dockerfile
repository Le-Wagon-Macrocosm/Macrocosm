# Backend — FastAPI inference service.
# Build context = backend/  ->  `docker build -t macrocosm-backend backend/`
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code
COPY . .

# run as non-root
RUN useradd -m appuser
USER appuser

# Cloud Run injects $PORT (default 8080); HF Spaces expects 7860.
# The model is loaded at startup from $MODEL_URI (e.g. gs://… on Cloud Run) — pass it at runtime.
ENV PORT=8080
EXPOSE 8080

# main.py lives at the build-context root -> module "main"
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
