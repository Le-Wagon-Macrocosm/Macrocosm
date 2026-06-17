# Tasks 2026-06-17 — image photo-z backend (plan & dependencies)

Build the **FastAPI backend** that serves a redshift from a **64×64×5 ugriz cutout**. A placeholder
model (`models/fake_image_model.pkl`, image → random z) lets us build and test the whole API **now**;
the real CNN drops in later with **no code change** (same `.predict` interface).

Each task implements one piece of `backend/`. Per-task workflow: **develop + test it in the task
notebook → move the working code into the matching `backend/*.py` → run the check → commit & push.**

## Task list
| # | folder | implements | target file |
|---|---|---|---|
| 01 | `01-config` | `Settings` (MODEL_PATH, IMG_SHAPE, TITLE) | `backend/config.py` |
| 02 | `02-schemas` | Pydantic request/response models | `backend/schemas.py` |
| 03 | `03-preprocessing` | `prepare_images()` validate + stack 64×64×5 | `backend/preprocessing.py` |
| 04 | `04-model-load` | `load_model()` / `get_model()` | `backend/model.py` |
| 05 | `05-health-endpoint` | FastAPI `app` + `GET /` | `backend/main.py` |
| 06 | `06-requirements` | runtime deps | `backend/requirements.txt` |
| 07 | `07-predict-fn` | `predict_z()` | `backend/model.py` |
| 08 | `08-predict-endpoint` | `POST /predict` | `backend/main.py` |
| 09 | `09-tests` | TestClient tests | `backend/tests/test_api.py` |
| 10 | `10-dockerfile` | container | `backend/Dockerfile` |
| 11 | `11-run-it` | end-to-end smoke (no code) | — |

## Dependency graph (which results feed which)
```
01 config ─────────────┐ (the others import settings)
02 schemas             │
03 preprocessing ──┐   │
04 model-load ─────┤   │
05 health-endpoint │   │ (uses app + model)
06 requirements    │   │
07 predict-fn  ←── 03 + 04
08 predict-endpoint ← 02 + 03 + 07
09 tests       ←── 08
10 dockerfile  ←── 06 + 08
11 run-it      ←── 05 + 08
```

## Waves (max parallelism)
- **Wave 1 — start now, 6 in parallel, no blockers:** `01` `02` `03` `04` `05` `06`
- **Wave 2 — once 03/04 (and 02) are in:** `07` then `08`
- **Wave 3 — once 08 is in:** `09` `10` `11`

> ⚠️ `04`+`07` both live in `model.py`, and `05`+`08` both live in `main.py`. Each task pushes its
> **own branch** `task/<folder>` and merges into `2026.6.17` via PR, so the two can't clobber each
> other — the second PR just merges (resolve the conflict if one shows up).

## Provided (do NOT implement — fixtures)
- `backend/fake_model.py` + `models/fake_image_model.pkl` — the placeholder image→z model.
- `backend/__init__.py`, `backend/tests/__init__.py`.

## Suggested owners (5 people, adjust freely)
| person | wave 1 | wave 2/3 |
|---|---|---|
| Hang | 05 health-endpoint | 08 predict-endpoint, 11 run-it (integrates) |
| Cathy | 04 model-load | 07 predict-fn |
| Mario | 03 preprocessing | 09 tests |
| Jose | 02 schemas | 10 dockerfile |
| Anastasia | 01 config + 06 requirements | floats / reviews |
