#!/usr/bin/env bash
# Download the placeholder image model from GCS (run from the repo root).
# The pickle is NOT committed to git; it lives in gs://macrocosm-lewagon/models/.
set -euo pipefail
mkdir -p models
gcloud storage cp gs://macrocosm-lewagon/models/fake_image_model.pkl models/fake_image_model.pkl
echo "got models/fake_image_model.pkl"
