# Macrocosm

Predicting galaxy **redshift** — and therefore distance — directly from cheap astronomical **images** (SDSS DR17 ugriz), with a FastAPI inference service and an interactive 3D web explorer.

> Le Wagon Data Science final project · 5-person team · 2-week build.

---

## Infrastructure

| Purpose | Tool / location |
|---|---|
| **Project management · tasks · Knowledge Base** | **YouTrack → https://macrocosm.youtrack.cloud/** |
| **Code** | GitHub org **`Le-Wagon-Macrocosm`**, repo **`Macrocosm`** (this repo) |
| **CI/CD** | GitHub Actions *(planned)* |
| **Model / data storage** | Google Cloud Storage bucket *(planned)* |
| **Deployment** | Cloud Run (primary) → Hugging Face Spaces (fallback) *(planned)* |
| **Training** | Colab + GPU *(offline; code lives in this repo)* |

### How to log in to YouTrack
Go to **https://macrocosm.youtrack.cloud/** and click **Log in with GitHub**.
You must be a member of the **`Le-Wagon-Macrocosm`** GitHub org — if you haven't accepted the org invite yet, check your GitHub notifications first.

> The **project plan, architecture, and all background docs live in the YouTrack Knowledge Base** (not here). This README only covers infrastructure + how to run the code.

---

## Repository layout

```
Macrocosm/
├── frontend/    # 3D web explorer (Three.js) + upload form
├── backend/     # FastAPI inference API (loads the model, serves /predict)
├── scripts/     # data pull, training, one-off utilities
├── Makefile     # single entrypoint: make install / pull / train / test / serve / deploy
└── README.md
```

## Getting started

```bash
make install   # install pinned dependencies
make help      # list all available commands
```

*(Targets are stubs for now — they'll be filled in as the code lands. Dependencies are pinned in `requirements.txt`.)*
