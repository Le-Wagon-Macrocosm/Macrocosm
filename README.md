# Macrocosm

Predicting galaxy **redshift** — and therefore distance — directly from cheap astronomical **images** (SDSS DR17 ugriz), with a FastAPI inference service and an interactive 3D web explorer.

> Le Wagon Data Science final project · 5-person team · 2-week build.

> 📚 The **project plan, architecture, modeling, and all background docs live in the YouTrack Knowledge Base** — https://macrocosm.youtrack.cloud/. This README only covers infrastructure + how to run the code.

---

## Infrastructure

| Purpose | Tool / location |
|---|---|
| **Tasks · timeline · Knowledge Base** | **YouTrack** → https://macrocosm.youtrack.cloud/ (log in with GitHub) |
| **Code** | GitHub org **`Le-Wagon-Macrocosm`**, repo **`Macrocosm`** (this repo) |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) — test on PR; deploy to Cloud Run (manual) via the `github-deployer` SA |
| **Data & model storage** | GCS **`gs://macrocosm-lewagon`** — `data/sample_v1/` (600k catalog + image shards) · `models/` · `mlflow/` |
| **Experiment tracking** | **MLflow** — VM-hosted, GitHub-org gated (see below) |
| **Image dataset build** | **SciServer Compute Jobs** (server-side cutouts → GCS) |
| **Training** | Colab + GPU (offline; code in this repo) |
| **Deployment** | Cloud Run (primary) → Hugging Face Spaces (fallback) |

GCP project: **`macrocosm-lewagon`** · region **`europe-west1`**. Services: Cloud Storage · Artifact Registry · Cloud Run · Compute Engine (the MLflow VM, CPU, stopped when idle). The lead adds you via IAM. Details → KB *GCP workflow*.

---

## MLflow tracking server

A shared MLflow server gated by **GitHub-org login**, on a small GCP VM you start only while training.

```bash
make mlflow-start          # start the VM (a few min to be ready); make mlflow-stop when done
make mlflow-url            # print the tracking URL
```

- **Browser** (view the UI): open the URL → log in with GitHub.
- **Colab / scripts** (log runs) — the client uses a shared bearer token (no browser flow); `scripts/train.py` already reads these:
  ```python
  import os
  os.environ["MLFLOW_TRACKING_URI"]   = "https://146-148-10-86.sslip.io"
  os.environ["MLFLOW_TRACKING_TOKEN"] = "<MLFLOW_API_TOKEN>"   # ask the lead
  ```

Full setup, lifecycle, and gotchas → KB *MLflow tracking server*.

---

## Repository layout

```
Macrocosm/
├── Makefile            # single entrypoint: install · backend · frontend · prepare-data · train · deploy · mlflow-*
├── scripts/            # freeze_catalog · prepare_data · run_job · build_shards · submit_jobs · pull_tabular · train · check_*
├── backend/            # FastAPI inference API (main.py · Dockerfile · requirements.txt)
├── frontend/           # 3D explorer (Three.js) + Dockerfile
├── mlflow/             # MLflow tracking server (docker-compose · Caddyfile · startup.sh)
├── .github/workflows/  # CI/CD
├── CONTRIBUTING.md     # branch / PR conventions
└── README.md
```

## Contributing / workflow

`main` is **protected**: branch off `main` → open a PR → green CI (`test`) → merge. Branch names `MCM-XX-short-slug`; reference the YouTrack issue (`MCM-XX`) in the PR. Never commit secrets / SA keys / `.env` / large data. See `CONTRIBUTING.md` + KB *Git workflow & repo governance*.

## Getting started

```bash
make help        # list all commands
make install     # local venv + backend deps (local testing only)
make backend     # run the FastAPI backend locally
```

Pinned deps in `backend/requirements.txt`. Some pipeline targets (`train`, `prepare-data`) run on Colab / SciServer — see the KB.
