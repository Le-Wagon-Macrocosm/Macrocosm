# Macrocosm — project entrypoint.
# Single command surface for the whole team. Fill in commands as the code lands.
.DEFAULT_GOAL := help

VENV := .venv
PIP  := $(VENV)/bin/pip

.PHONY: help install backend frontend prepare-data train test docker-build publish-backend publish-frontend deploy clean

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

# ===== local dev (NO Docker) — the venv is for local testing only; Docker installs deps itself =====

$(VENV)/bin/uvicorn: backend/requirements.txt   # (re)create venv + install backend deps when reqs change
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

install: $(VENV)/bin/uvicorn  ## set up the local venv + backend deps (local testing only)

backend: install  ## run the FastAPI backend locally (venv + auto-reload)
	$(VENV)/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

frontend:  ## run the Three.js frontend locally (node dev server)
	cd frontend && npm install && npm run dev

clean:  ## remove the local venv
	rm -rf $(VENV)

# ===== pipeline (stubs) =====

prepare-data:  ## pull + preprocess + freeze the SDSS dataset (scripts/)
	@echo "TODO: python -m scripts.prepare_data"

train:  ## train the model (baseline / CNN)
	@echo "TODO: python -m scripts.train"

test:  ## run tests
	@echo "TODO: pytest"

# ===== docker / deploy (NO venv — image installs deps directly) =====
# Override on the CLI, e.g.  make deploy PROJECT=my-gcp-proj MODEL_URI=gs://bucket/model.pkl
PROJECT   ?= macrocosm-lewagon
REGION    ?= europe-west1
SERVICE   ?= macrocosm-backend
MODEL_URI ?= gs://macrocosm-lewagon/models/model.pkl

# Artifact Registry image coordinates:  REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG
AR_REPO        ?= macrocosm
TAG            ?= latest
AR_HOST        := $(REGION)-docker.pkg.dev
BACKEND_IMAGE  := $(AR_HOST)/$(PROJECT)/$(AR_REPO)/macrocosm-backend
FRONTEND_IMAGE := $(AR_HOST)/$(PROJECT)/$(AR_REPO)/macrocosm-frontend

docker-build:  ## build the backend image locally (simple tag, for local docker run)
	docker build -t $(SERVICE) backend/

publish-backend:  ## build + push the backend image to Artifact Registry
	docker build -t $(BACKEND_IMAGE):$(TAG) backend/
	docker push $(BACKEND_IMAGE):$(TAG)

publish-frontend:  ## build + push the frontend image to Artifact Registry
	docker build -t $(FRONTEND_IMAGE):$(TAG) frontend/
	docker push $(FRONTEND_IMAGE):$(TAG)

deploy: publish-backend  ## push the backend image, then deploy it to Cloud Run
	gcloud run deploy $(SERVICE) \
		--image $(BACKEND_IMAGE):$(TAG) \
		--project $(PROJECT) \
		--region $(REGION) \
		--port 8080 \
		--set-env-vars MODEL_URI=$(MODEL_URI) \
		--memory 1Gi \
		--cpu 1 \
		--min-instances 0 \
		--max-instances 3 \
		--allow-unauthenticated

# One-time setup:
#   gcloud auth login
#   gcloud services enable run.googleapis.com artifactregistry.googleapis.com
#   gcloud artifacts repositories create $(AR_REPO) --repository-format=docker --location=$(REGION) --project=$(PROJECT)
#   gcloud auth configure-docker $(AR_HOST)      # let docker push to Artifact Registry
#   grant the Cloud Run service account "Storage Object Viewer" on the model bucket (reads MODEL_URI)
