# Macrocosm — project entrypoint.
# Single command surface for the whole team. Fill in commands as the code lands.
.DEFAULT_GOAL := help

# Local dev uses pyenv + Python 3.10.6 (Le Wagon standard). The committed
# `.python-version` (virtualenv name `macrocosm`) auto-activates it in this dir.

.PHONY: help install backend frontend prepare-data train test docker-build publish-backend publish-frontend deploy clean mlflow-create mlflow-start mlflow-stop mlflow-url

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

# ===== local dev (NO Docker) — runs in your active pyenv virtualenv =====

install:  ## install dev deps into the active virtualenv (needs `pyenv local macrocosm` first)
	@python -c 'import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)' || { echo ">> No virtualenv active. Run:  pyenv virtualenv 3.10.6 macrocosm && pyenv local macrocosm"; exit 1; }
	pip install --upgrade pip
	pip install -r requirements.txt          # local dev / data-science stack (pulls in backend deps)

backend: install  ## run the FastAPI backend locally (auto-reload)
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

frontend:  ## run the Three.js frontend locally (node dev server)
	cd frontend && npm install && npm run dev

clean:  ## remove python caches (the virtualenv is managed by pyenv: `pyenv uninstall macrocosm`)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# ===== pipeline (stubs) =====

prepare-data:  ## build image stamps -> GCS (run ON SciServer, per shard)
	@echo "Run on SciServer. Step A (once):  python scripts/freeze_catalog.py"
	@echo "Step B (per shard i of K):"
	@echo "  python scripts/prepare_data.py --catalog gs://$(PROJECT)/data/sample_v1/catalog_v1.parquet \\"
	@echo "    --key <sa-key.json> --of 64 --shard <i>"

train:  ## train the model (baseline / CNN)
	@echo "TODO: python -m scripts.train"

test:  ## run tests
	@echo "TODO: pytest"

# ===== docker / deploy (NO venv — image installs deps directly) =====
# Override on the CLI, e.g.  make deploy PROJECT=my-gcp-proj GCS_KEY=path/to/key.json
PROJECT   ?= macrocosm-lewagon
REGION    ?= europe-west1
SERVICE   ?= macrocosm-backend
# SA key (Storage Object Viewer on the model bucket) used ONLY at build time to pull the
# pickles into the image via a BuildKit secret. Never baked into a layer. Keep it gitignored.
# In CI this is the same GCP_SA_KEY used to deploy; locally, point it at any key with bucket read.
GCS_KEY   ?= gcp-sa-key.json

# Artifact Registry image coordinates:  REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG
AR_REPO        ?= macrocosm
TAG            ?= latest
AR_HOST        := $(REGION)-docker.pkg.dev
BACKEND_IMAGE  := $(AR_HOST)/$(PROJECT)/$(AR_REPO)/macrocosm-backend
FRONTEND_IMAGE := $(AR_HOST)/$(PROJECT)/$(AR_REPO)/macrocosm-frontend

# BuildKit is required for the --secret mount that feeds the GCS key to the image build.
DOCKER_BUILD = DOCKER_BUILDKIT=1 docker build -f backend/Dockerfile --secret id=gcs_key,src=$(GCS_KEY)

docker-build:  ## build the backend image locally (pulls models from GCS via the build secret)
	$(DOCKER_BUILD) -t $(SERVICE) .

publish-backend:  ## build + push the backend image to Artifact Registry
	$(DOCKER_BUILD) -t $(BACKEND_IMAGE):$(TAG) .
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
		--memory 8Gi \
		--cpu 2 \
		--cpu-boost \
		--min-instances 0 \
		--max-instances 3 \
		--allow-unauthenticated
# Memory: the StackingRegressor (RandomForest on ~550k rows) needs several GiB once unpickled
# (transient decompression peak is higher); 1-4 GiB OOMs at startup. --cpu-boost speeds the load.

# One-time setup:
#   gcloud auth login
#   gcloud services enable run.googleapis.com artifactregistry.googleapis.com
#   gcloud artifacts repositories create $(AR_REPO) --repository-format=docker --location=$(REGION) --project=$(PROJECT)
#   gcloud auth configure-docker $(AR_HOST)      # let docker push to Artifact Registry
#   grant the BUILD service account ($(GCS_KEY)) "Storage Object Viewer" on the model bucket
#   (the models are baked into the image at build time, so Cloud Run itself needs no GCS access)

# ===== MLflow tracking server on a GCP VM (see mlflow/ + KB MCM-A-14) =====
MLFLOW_VM   ?= macrocosm-mlflow
MLFLOW_ZONE ?= europe-west1-b
MLFLOW_IP   ?= macrocosm-mlflow-ip

mlflow-create:  ## one-time: reserve static IP + create VM + open 80/443 (then deploy compose, see mlflow/README)
	gcloud services enable compute.googleapis.com --project $(PROJECT)
	-gcloud compute addresses create $(MLFLOW_IP) --region $(REGION) --project $(PROJECT)
	-gcloud compute firewall-rules create macrocosm-mlflow-web --project $(PROJECT) \
		--allow tcp:80,tcp:443 --direction INGRESS --target-tags mlflow
	gcloud compute instances create $(MLFLOW_VM) --project $(PROJECT) --zone $(MLFLOW_ZONE) \
		--machine-type e2-medium --tags mlflow \
		--image-family ubuntu-2204-lts --image-project ubuntu-os-cloud \
		--scopes cloud-platform \
		--address $$(gcloud compute addresses describe $(MLFLOW_IP) --region $(REGION) --project $(PROJECT) --format='value(address)') \
		--metadata-from-file startup-script=mlflow/startup.sh
	@$(MAKE) mlflow-url

mlflow-start:  ## start the MLflow VM (compose auto-restarts; ~a few min to be ready)
	gcloud compute instances start $(MLFLOW_VM) --zone $(MLFLOW_ZONE) --project $(PROJECT)
	@$(MAKE) mlflow-url

mlflow-stop:  ## stop the MLflow VM (pauses compute billing; static IP + run data kept)
	gcloud compute instances stop $(MLFLOW_VM) --zone $(MLFLOW_ZONE) --project $(PROJECT)

mlflow-url:  ## print the tracking URL (export MLFLOW_TRACKING_URI to this)
	@IP=$$(gcloud compute addresses describe $(MLFLOW_IP) --region $(REGION) --project $(PROJECT) --format='value(address)' 2>/dev/null); \
	echo "MLFLOW_TRACKING_URI=https://$$(echo $$IP | tr . -).sslip.io"
