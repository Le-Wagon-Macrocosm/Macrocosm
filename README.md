# Macrocosm

**Predicting galaxy redshift from astronomical images — and placing every galaxy in a 3D universe you can explore.**

Macrocosm uses a deep learning fusion model to estimate galaxy redshift (z) directly from 5-band SDSS ugriz cutouts, with optional photometric features for higher accuracy. Predictions are rendered in real time in an interactive 3D web explorer that maps each galaxy's true cosmic distance.

> Le Wagon Data Science final project · 5-person team · 2-week build

**[Live Demo →](https://le-wagon-macrocosm.github.io/Macrocosm)**

---

## What it does

Upload a galaxy image (or use one of our sample galaxies), adjust the available photometric measurements, and Macrocosm will:

1. **Predict the redshift** (z) using a CNN + Mixture Density Network fusion model
2. **Explain the prediction** with a Grad-CAM saliency map highlighting which pixels drove the estimate
3. **Place the galaxy** in a live 3D scene — color-coded by redshift, positioned by its inferred distance in gigalight-years

---

## Model Architecture

The system uses a three-stage fusion pipeline trained on ~600k SDSS DR17 galaxies (0 < z < 0.4):

```
Galaxy image (24×24×5 ugriz)
    └─► Image CNN ──────────────────────────────► 64-d embedding
                                                         │
Tabular features (up to 11 SDSS fields)                  │
    └─► Tabular Stack (RF + HGB + MLP) ─► 3 predictions  │
                  + presence mask (16-d) ────────────────►│
                                                          ▼
                                             Fusion MLP + MDN (K=5)
                                                          │
                                                          ▼
                                             ẑ  (redshift point estimate)
                                          + σ  (per-component uncertainty)
```

**Graceful degradation:** if more than 3 tabular features are missing, the model falls back to the image-only CNN path automatically.

**Training details:**
- Image CNN: 24×24×5 → 64-d embedding, trained with an MDN head (log1p redshift space)
- Tabular baseline: stacked ensemble of Random Forest, Histogram Gradient Boosting, and MLP
- Fusion head: 83-d vector [3 base predictions | 16-d presence mask | 64-d image embedding] → MDN (5 Gaussian components)
- Data: SDSS DR17 spectroscopic catalog, 24×24 pixel ugriz cutouts via SciServer

---

## Tech Stack

| Layer | Technology |
|---|---|
| **ML / Training** | TensorFlow / Keras, scikit-learn, MLflow, Colab + GPU |
| **Inference API** | FastAPI, Uvicorn, Astropy |
| **3D Frontend** | Three.js, Vite, Vanilla JS |
| **Data Pipeline** | SciServer Compute Jobs, GCS, pandas |
| **Infrastructure** | GCP Cloud Run (backend), GitHub Pages (frontend), Artifact Registry |
| **CI/CD** | GitHub Actions |

---

## API

The backend exposes three endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check — returns loaded model names and input shape |
| `POST` | `/predict` | Multipart: `.npy` image + optional JSON tabular fields → `{ z, distance_gly, ... }` |
| `POST` | `/explain` | Same as `/predict` + Grad-CAM saliency heatmap |

---

## Local Development

**Requirements:** Python 3.12, pyenv, Node.js ≥ 18, Docker (for deployment only)

### Backend

```bash
git clone https://github.com/Le-Wagon-Macrocosm/Macrocosm.git && cd Macrocosm

pyenv virtualenv 3.12.9 upgrade_macro
pyenv local upgrade_macro

cp .env.sample .env
# edit .env: set GOOGLE_CLOUD_PROJECT=macrocosm-lewagon

gcloud auth application-default login
gcloud auth application-default set-quota-project macrocosm-lewagon

make install
make backend        # FastAPI on http://localhost:8000
```

To run without GCS access (no real model artifacts needed):

```bash
bash scripts/get_fake_model.sh   # downloads stub models for local testing
make backend
```

### Frontend

```bash
make frontend       # Vite dev server on http://localhost:5173
```

The frontend reads `VITE_API_BASE` to point at the backend. In development it defaults to `http://localhost:8000`.

### Tests

```bash
pytest -q backend/tests/
```

---

## Repository Layout

```
Macrocosm/
├── backend/            # FastAPI inference service
│   ├── main.py         # API routes (/predict, /explain, health)
│   ├── model.py        # Model loading, fusion prediction, MDN decoding
│   ├── features.py     # Tabular feature engineering + imputation
│   ├── gradcam.py      # Grad-CAM saliency
│   ├── cosmology.py    # z → distance conversions (comoving, light-travel, luminosity)
│   └── Dockerfile
├── frontend/           # Three.js 3D galaxy explorer
│   └── src/
│       ├── scene.js    # 3D scene (color = redshift, radius = distance)
│       ├── api.js      # Fetch wrappers for the backend
│       └── galaxyImage.js  # .npy → WebGL texture decoder
├── scripts/            # Data pipeline + training utilities
│   ├── freeze_catalog.py   # SDSS DR17 catalog pull
│   ├── prepare_data.py     # Galaxy image cutout stamping (SciServer)
│   └── train.py            # CNN + fusion training (Colab target)
├── mlflow/             # Self-hosted MLflow tracking server (GCP VM)
├── Makefile            # Single entrypoint for all workflows
└── .env.sample         # Configuration template
```

---

## Deployment

```bash
make deploy           # Build Docker image → push to Artifact Registry → deploy to Cloud Run
```

The frontend deploys automatically to GitHub Pages on every push to `main` that touches `frontend/`.

---

## Team

Built at [Le Wagon](https://www.lewagon.com/) Data Science bootcamp, June 2026.

| | |
|---|---|
| Jose Bagina | |
| *[teammate]* | |
| *[teammate]* | |
| *[teammate]* | |
| *[teammate]* | |
