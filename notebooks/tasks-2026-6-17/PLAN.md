# Tasks 2026-06-17 — fused photo-z backend (plan & dependencies)

Build the **FastAPI backend** that serves a redshift from a **64×64×5 ugriz cutout + optional tabular**.
The final model **fuses image + tabular** (KB *Architecture*); we ship it as a single `POST /predict`.
**Placeholder today:** the real trained tabular baseline (`baseline_stack.pkl`) handles the tabular
branch; a fake random-z model stands in for the image CNN. When the fused CNN artifact lands it
**replaces the model with no API change**.

## Single contract (KB *Architecture* / *Frontend UI spec*)
```
POST /predict  multipart/form-data
  file        : .npy (64,64,5) ugriz cutout      (required)
  ra, dec     : floats                            (required, for 3D placement)
  tabular     : optional JSON catalog row         (engineered -> 16 features -> baseline)
-> { "z": .., "distance_gly": .., "z_lo": null, "z_hi": null }
```

## Task list
| Wave | # | folder | implements | target |
|---|---|---|---|---|
| 1 | 01 | 01-config | Implement `Settings | `backend/config.py` |
| 1 | 02 | 02-features-tabular | tabular_features(row) | `backend/features.py` |
| 1 | 03 | 03-features-image | preprocess_image(arr, crop) | `backend/features.py` |
| 1 | 04 | 04-schemas | Pydantic `TabularInput` + `PredictRespon | `backend/schemas.py` |
| 1 | 05 | 05-cosmology | z_to_distance_gly(z)` via astropy Planck | `backend/cosmology.py` |
| 1 | 06 | 06-model-load | load_models()` / `get_models() | `backend/model.py` |
| 1 | 07 | 07-health-endpoint | FastAPI `app` + lifespan + CORS + `GET / | `backend/main.py` |
| 1 | 08 | 08-requirements | backend/requirements.txt | `backend/requirements.txt` |
| 2 | 09 | 09-predict-fn | predict_z(images, tabular) | `backend/model.py` |
| 2 | 10 | 10-predict-endpoint | POST /predict | `backend/main.py` |
| 3 | 11 | 11-tests | TestClient API tests. | `backend/tests/test_api.py` |
| 3 | 12 | 12-dockerfile | Containerize the API (bakes in both mode | `backend/Dockerfile` |
| 3 | 13 | 13-run-it | End-to-end smoke with the REAL baseline  | `—` |

## Dependency / waves
- **Wave 1 (start now, 8 in parallel):** 01 config · 02 tabular-features · 03 image-preprocess · 04 schemas · 05 cosmology · 06 model-load · 07 health-endpoint · 08 requirements
- **Wave 2:** 09 predict-fn (needs 02/03/06) → 10 predict-endpoint (needs 04/05/09)
- **Wave 3:** 11 tests · 12 dockerfile · 13 run-it (end-to-end, real baseline)

> Shared files — each task pushes its **own branch** `task/<folder>` and merges via PR, so these can't
> clobber each other: **02+03** → `features.py`, **06+09** → `model.py`, **07+10** → `main.py`.

## Provided (do NOT implement — fixtures)
- `backend/fake_model.py` + `models/fake_image_model.pkl` — the placeholder image model.
- `models/baseline_stack.pkl` — the **real** trained tabular baseline (pulled from GCS; not in git).
- `backend/__init__.py`, `backend/tests/__init__.py`.

## Suggested owners (5 people, rotate freely)
| person | wave 1 | wave 2/3 |
|---|---|---|
| Hang | 07 health-endpoint | 10 predict-endpoint, 13 run-it |
| Cathy | 06 model-load | 09 predict-fn |
| Mario | 02 tabular-features | 11 tests |
| Jose | 03 image-preprocess | 12 dockerfile |
| Anastasia | 01 config + 04 schemas + 05 cosmology + 08 requirements | floats / reviews |
