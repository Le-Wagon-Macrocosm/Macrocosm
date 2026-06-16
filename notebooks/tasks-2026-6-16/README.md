# Macrocosm photo-z — outlier study tasks (2026-06-16)

A set of small, self-contained experiments on **catastrophic outliers** in tabular photo-z. See
**`PLAN.md`** for the dependency graph, waves, and suggested owners.

## Given facts (do not re-derive)
- **Catalog:** `gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet` (600k rows, 55 columns).
  Clean the SDSS **`-9999`** sentinel ("not measured") to NaN before anything.
- **Hard set:** a 400k 5-fold CV with three models (HGB, RF, MLP) already identified **6,974 galaxies**
  that *all three* fail on out-of-fold (|Δz/(1+z)| > 0.05). Their objids are in **`hard_objids.csv`**.
  Use it as a fixed input — do **not** re-run the 400k job.
- **SciServer CV output:** the full 400k out-of-fold predictions + metrics are bundled at
  `gs://macrocosm-lewagon/results/outlier_cv_results.tar.gz` (**on GCS, not in git** — too big).
  **Task 00** downloads and analyzes it; that's where the ceiling and the hard set come from.
- **Metric:** `σ_MAD = 1.4826·median(|Δz − median(Δz)|)`, `Δz = (z_pred − z_true)/(1+z)`; outlier = |Δz| > 0.05.
  Report σ_MAD **and** outlier rate.

## Conventions (so everyone's numbers line up)
- Subsample with the seeds written in each task (`load_features(n=100000, seed=1)` for the modelling tasks).
- `KFold(3, shuffle=True, random_state=42)`.
- Model configs are given in Task 02 — reuse them verbatim.

## Workflow
1. `git pull origin 2026.6.16`
2. open your task's `task.ipynb`, fill the `# YOUR CODE HERE` cells
3. run the `write_report(...)` cell → it writes `report.md`
4. run the last cell → commits & pushes `task.ipynb` + `report.md` to `2026.6.16`

## Reading the catalog
- **Colab:** `from google.colab import auth; auth.authenticate_user()` then read the `gs://` path.
- **Local:** `gcloud storage cp gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet .` once, then
  point `CATALOG` at the local file.
