# Development Guide

Internal setup and workflow reference for the Macrocosm team.

---

## Infrastructure

| Purpose | Tool / location |
|---|---|
| **Tasks · timeline · Knowledge Base** | YouTrack → https://macrocosm.youtrack.cloud/ (log in with GitHub) |
| **Code** | GitHub org `Le-Wagon-Macrocosm`, repo `Macrocosm` (this repo) |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) — test on PR; deploy to Cloud Run (manual) |
| **Data & model storage** | GCS `gs://macrocosm-lewagon` — `data/sample_v1/` (catalog + image shards) · `models/` · `mlflow/` |
| **Experiment tracking** | MLflow — VM-hosted, GitHub-org gated (see below) |
| **Image dataset build** | SciServer Compute Jobs (server-side cutouts → GCS) |
| **Training** | Colab + GPU (offline; code in `scripts/train.py`) |
| **Deployment** | Cloud Run (primary) → Hugging Face Spaces (fallback) |

GCP project: `macrocosm-lewagon` · region `europe-west1`. The lead adds you via IAM. Details → KB *GCP workflow*.

---

## Local Setup (one-time)

We use **pyenv** + Python **3.12.9**. The committed `.python-version` (virtualenv name `upgrade_macro`) auto-activates it in this directory.

```bash
git clone https://github.com/Le-Wagon-Macrocosm/Macrocosm.git && cd Macrocosm

pyenv virtualenv 3.12.9 upgrade_macro   # create the project virtualenv
pyenv local upgrade_macro               # auto-activate it here

make install                            # pip install -r requirements.txt
```

`requirements.txt` = local dev + data science stack (pulls in backend deps). `backend/requirements.txt` = lean runtime deps shipped in the Docker image.

---

## Environment & GCS Access

Config lives in a single `.env` (gitignored). GCS access uses your own Google account — your Gmail has IAM on the bucket, so no shared key is needed.

```bash
cp .env.sample .env    # edit GOOGLE_CLOUD_PROJECT if needed; leave GOOGLE_APPLICATION_CREDENTIALS unset
```

Authenticate:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project macrocosm-lewagon
```

Load the `.env` in your shell:
- **VS Code**: the Python/Jupyter extension reads `.env` automatically. Reload the window after editing.
- **Terminal (zsh + direnv)**: `direnv allow .` (install once: `brew install direnv` / `sudo apt install -y direnv`, then add `eval "$(direnv hook zsh)"` to your `.zshrc`).

Verify access from your venv:

```python
import gcsfs, os
print(gcsfs.GCSFileSystem().ls("macrocosm-lewagon/data/sample_v1")[:3])
```

**`403 Forbidden`?** The usual cause is `GOOGLE_APPLICATION_CREDENTIALS` being set (often left over from a Le Wagon bootcamp challenge), which overrides your personal login. Fix: `unset GOOGLE_APPLICATION_CREDENTIALS` and remove it from `.env`/`.zshrc`, then re-run `gcloud auth application-default login`. Last resort: use the shared `sciserver-uploader.json` key (see the commented line in `.env.sample`). Never commit `.env` or any `*.json` key.

---

## Running Locally

```bash
make backend     # FastAPI on http://localhost:8000 (auto-reload)
make frontend    # Vite dev server on http://localhost:5173
```

To run without real model artifacts (no GCS access needed):

```bash
bash scripts/get_fake_model.sh   # downloads stub models
make backend
```

---

## Tests

```bash
pytest -q backend/tests/
```

CI downloads real model artifacts from GCS before running. Locally, stub models from `get_fake_model.sh` are sufficient for contract tests.

---

## MLflow Tracking Server

A shared MLflow server gated by GitHub-org login, running on a small GCP VM you start only while training.

```bash
make mlflow-start    # start the VM (a few min to be ready)
make mlflow-url      # print the tracking URL
make mlflow-stop     # stop when done (pauses compute billing; data is kept)
```

**Browser (view UI):** open the URL → log in with GitHub.

**Colab / scripts (log runs):** the client uses a bearer token — ask the lead for `MLFLOW_API_TOKEN`.

```python
import os
os.environ["MLFLOW_TRACKING_URI"]   = "https://146-148-10-86.sslip.io"
os.environ["MLFLOW_TRACKING_TOKEN"] = "<MLFLOW_API_TOKEN>"
```

Full setup and gotchas → KB *MLflow tracking server*.

---

## Deployment

```bash
make deploy        # build Docker image → push to Artifact Registry → deploy to Cloud Run
```

The frontend deploys automatically to GitHub Pages on every push to `main` that touches `frontend/`.

---

## Contributing

See `CONTRIBUTING.md` for branch naming, PR flow, and commit conventions. The short version: branch off `main` as `MCM-XX-short-slug`, open a PR, wait for green CI, then merge. No direct pushes to `main`.
