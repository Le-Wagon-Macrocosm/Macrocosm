# Tasks 2026-06-16 — plan & dependencies

9 experiments on the photo-z **outlier study**. The hard set (6,974 galaxies that all models fail on,
found from a 400k 5-fold CV) is **GIVEN** in `hard_objids.csv` — nobody re-runs that 400k job.
Most tasks are **~100k / 3-fold** (a few minutes each) and **self-contained** (its `task.ipynb` re-loads,
cleans and builds features on its own), so any task can *run* in isolation. The dependencies below are
about which **results inform or are compared-to** which.

Task **00** is different: it analyzes the **pre-computed SciServer output** (the 400k out-of-fold
predictions), which lives as a tarball **on GCS, not in git**:
`gs://macrocosm-lewagon/results/outlier_cv_results.tar.gz` (the task notebook downloads it).

## Task list
| # | folder | one-liner |
|---|---|---|
| 00 | `00-cv-results-analysis` | analyze the SciServer 400k-CV output (OOF preds) → ceiling + source of the hard set |
| 01 | `01-feature-engineering` | clean -9999, build the 16 features, sanity-check distributions |
| 02 | `02-baseline-models` | LR / RF / HGB / MLP, 100k 3-fold, σ_MAD + outlier rate (the reference numbers) |
| 03 | `03-dz-distribution` | Δz of the hard set: one-sided bias or two-sided scatter? |
| 04 | `04-hard-set-anatomy` | compare all 55 columns hard-vs-normal → *why* are they hard? |
| 05 | `05-remove-outliers-training` | drop hard from training; does it help normal galaxies? per model |
| 06 | `06-stacking` | stack RF+HGB+MLP → LinearRegression; vs single models |
| 07 | `07-stacking-clean` | stacking + remove-outliers-from-training; where does the gain land? |
| 08 | `08-error-aware-features` | add `modelMagErr_*` / 1·err⁻² weighting; does it help? |

## Dependency graph (results, not execution)
```
00 cv-results-analysis    (foundational · downloads SciServer output · derives the ceiling + hard set)
01 feature-engineering ─┐ (the feature recipe everyone reuses)
02 baseline-models     ─┴─> reference σ_MAD/outlier for 05, 06, 08
03 dz-distribution        (independent · uses GIVEN hard set)
04 hard-set-anatomy       (independent · uses GIVEN hard set) ──> motivates 08
05 remove-outliers-train  (compares to 02) ─┐
06 stacking               (compares to 02) ─┴─> 07 stacking-clean
08 error-aware            (needs 04's "it's noise" finding + 02 baseline)
```

## Waves (for maximum parallelism)
- **Wave 0 — foundational (sets the context for everyone):** `00`
- **Wave 1 — start immediately, no blockers:** `01`, `02`, `03`, `04`
- **Wave 2 — once 02's baseline numbers exist:** `05`, `06`, `08`
- **Wave 3 — once 05 + 06 are done:** `07`

**Critical path:** `02 → 06 → 07` (and `02 → 05 → 07`). 07 is the only task that genuinely waits on two others.

## Suggested owners (5 people — adjust freely)
| person | wave 0/1 | wave 2/3 |
|---|---|---|
| Hang | **00 cv-results** (sets context) | floats, integrates, reviews |
| Cathy | 02 baselines | 06 stacking |
| Mario | 01 features | 05 remove-outliers |
| Jose | 03 dz-distribution | 08 error-aware |
| Anastasia | 04 hard-anatomy | 07 stacking-clean (pairs with 05/06 owners) |

## How each task works
1. Open `NN-…/task.ipynb`, answer the `❓ Question` cells (`# YOUR CODE HERE`).
2. Fill the `write_report(...)` call with your results + a 2-3 sentence conclusion, run it → it regenerates `report.md`.
3. Run the **last cell** to `git add task.ipynb report.md && git commit && git push origin 2026.6.16`.
4. `git pull origin 2026.6.16` before you start so you have everyone else's work.

> This file is the basis for the YouTrack tasks — one YT issue per row above, with the wave as the sprint order.
