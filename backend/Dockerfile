# syntax=docker/dockerfile:1
# Serving image for the photo-z API. Build from the REPO ROOT with BuildKit, passing a
# GCS service-account key (Storage Object Viewer on the model bucket) as a SECRET so the
# model pickles are pulled at build time. The key is mounted only for that one RUN and is
# never written to an image layer:
#   DOCKER_BUILDKIT=1 docker build -f backend/Dockerfile \
#     --secret id=gcs_key,src=gcp-sa-key.json -t macrocosm-backend .

# --- stage 1: pull the model artifacts from GCS (throwaway; has the SA key + gcs client) ---
# v4 fusion stack: tabular bases (664MB) + image CNN + fusion head + tabular medians.
FROM python:3.12-slim AS models
RUN pip install --no-cache-dir google-cloud-storage
RUN --mount=type=secret,id=gcs_key \
    GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcs_key \
    python -c "import os; from google.cloud import storage; os.makedirs('/models', exist_ok=True); b=storage.Client().bucket('macrocosm-lewagon'); [b.blob('models/'+n).download_to_filename('/models/'+n) for n in ('baseline_stack_v4.pkl','photoz_cnn_v4.h5','fusion_v4.keras','tabular_medians_v4.npy')]"

# --- stage 2: runtime image (no SA key, no gcs client baked in) ---
FROM python:3.12-slim
WORKDIR /app

# Deps first for layer caching. requirements pins scikit-learn to the pickle's version
# (1.9.0), whose Python>=3.11 floor is satisfied by python:3.12.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=models /models ./models

ENV BASELINE_PATH=models/baseline_stack_v4.pkl \
    CNN_MODEL_PATH=models/photoz_cnn_v4.h5 \
    FUSION_MODEL_PATH=models/fusion_v4.keras \
    MEDIANS_PATH=models/tabular_medians_v4.npy

# Cloud Run sets $PORT (defaults to 8080) and routes to it; fall back to 8080 locally.
EXPOSE 8080
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
