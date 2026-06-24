#!/usr/bin/env bash
# Pull the model artifacts from GCS into models/ (run from the repo root). Needs gcloud auth.
set -e
mkdir -p models
gcloud storage cp gs://macrocosm-lewagon/models/fake_image_model.pkl models/fake_image_model.pkl
if [ "$1" = "--baseline" ]; then
  echo "pulling the 657MB real baseline..."
  gcloud storage cp gs://macrocosm-lewagon/models/baseline_stack.pkl models/baseline_stack.pkl
fi
echo "models ready: $(ls models/*.pkl)"
