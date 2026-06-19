# Serving image for the FastAPI photo-z API.
# Build from the REPO ROOT (the COPY paths below are repo-relative):
#   docker build -f backend/Dockerfile -t macrocosm-api .
FROM python:3.12-slim

WORKDIR /app

# Deps first for layer caching. requirements pins scikit-learn to the pickle's
# version (1.9.0), whose Python>=3.11 floor is satisfied by python:3.12.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code + the two model artifacts the lifespan loads.
COPY backend/ ./backend/
COPY models/baseline_stack.pkl models/fake_image_model.pkl ./models/

# Paths the app reads (config.py honors these env vars).
ENV BASELINE_PATH=models/baseline_stack.pkl \
    IMAGE_MODEL_PATH=models/fake_image_model.pkl

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
