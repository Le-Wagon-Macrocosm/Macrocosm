# Outlier Analysis — Research Plan

> Tabular photo-z. Why do ~1.5% of galaxies resist *every* tabular model, and can anything be done?
> Scratch/working doc — not the KB.

## Central question
A small population (~1.5%) is flagged as a catastrophic outlier (|Δz/(1+z)| > 0.05) by **all three**
models (LR, RF, MLP) at once, out-of-fold, and stays wrong even after adding 60% of them to training.
**What causes it, and what (if anything) fixes it?**

## Priors (from earlier runs)
- All-3-model outlier **intersection ≈ 1.5%** of galaxies; stable across 400k 5-fold CV (fold0 = 1214, fold1 = 1180).
- These cases are **faint** (dered_r ≈ 20, +2.6 mag vs normal), **noisy** (modelMagErr 4–5× normal), slightly higher z.
- Colors (r-i, i-z) are smeared → injecting 60% into training barely helps → **error is largely irreducible**.
- Single-model σ_MAD: LR 0.024, RF 0.014, MLP 0.0136. Outlier rate: LR 7.7%, RF 3.1%, MLP 2.7%.

## Four candidate explanations (the whole analysis exists to separate these)
| Tag | Hypothesis | Decisive evidence | If true, do this |
|---|---|---|---|
| **H-noise** | faint → low S/N → colors drowned in photometric noise | `*Err` high, mags faint | error-aware model / S/N cut; **images also weak** |
| **H-degeneracy** | genuine color↔z degeneracy (bright galaxies, ambiguous colors) | outliers exist at the **bright** end too, `*Err` not high | **images can help** (morphology breaks it) |
| **H-label** | the spectroscopic z (our ground truth) is itself uncertain | `zErr` high in the hard set | not a model failure; weight/cut by label quality |
| **H-instrument** | specific runs/fields have bad photometry | `ra/dec/run/camcol/field` stand out | data-quality cut, revisit the freeze step |

---

## Experiment 1 — CV stability + metrics + Δz distributions
**Goal:** robustly establish (a) the intersection fraction is fold-stable, (b) the OOF hard population,
(c) per-fold per-model MAE / σ_MAD / outlier-rate **with CV error bars** (missing from the first run),
(d) **the Δz distribution of hard vs full population under RF and MLP** (newly requested data).

**Method:** KFold(n). Each fold: train LR/RF/MLP on the 4 training folds, predict the held-out fold.
Record per-model metrics + the 3-model outlier intersection. Save the **OOF prediction** for every galaxy
(each tested exactly once) → compute per-galaxy Δz = (z_pred − z_true)/(1+z) for each model.

**Data to collect:**
- metrics table: MAE / σ_MAD / outlier-rate, mean ± std across folds, per model
- hard objids (OOF all-3 intersection) → `hard_outliers_cv.csv`
- **Δz histograms: hard vs full, for RF and MLP** (overlay, mark ±0.05 thresholds)

**Predictions:**
- intersection ≈ 1.5% ± tiny; σ_MAD fold-std small (320k train is plenty).
- strong models (RF/MLP) overlap ~55%; low overlap with LR.
- hard-set Δz is **broad / heavy-tailed** and likely **skewed negative** (faint high-z galaxies get
  *under*-predicted — pulled toward the crowded low-z region). Full-set Δz is a tight spike at 0.

**Decision tree:**
- Stable → hard set is an intrinsic, well-defined population → proceed to Exp 2/3.
- Fold-to-fold noisy → partly *model variance*, not data → run **repeated-KFold (multi-seed)**, keep only
  galaxies flagged as outliers in a majority of repeats, then continue.
- Hard-set Δz strongly one-sided → a **systematic bias** (regression to the mean) → a bias-correction or
  quantile/asymmetric loss might recover some; symmetric heavy tails → pure scatter, not correctable.

---

## Experiment 2 — remove the outlier population from training (keep it in test)
**Goal:** are the hard/noisy outliers *polluting* training (dragging the fit on normal galaxies)?

**Method (leakage-safe):**
1. Define outlier set **O** from Exp 1's **OOF labels** (a galaxy's label comes from when it was held out).
2. New CV: each fold trains on (train folds **− O**); the **test fold stays intact**.
3. Report test metrics **split** into `test∖O` (normal) and `test∩O` (hard) separately.
4. **Dose gradient:** O at three widths — strict (all-3 ≈ 1.5%), medium (RF outliers ≈ 3%), wide (any-model ≈ 8%).

**Predictions:**
- H2a (most likely): normal-galaxy σ_MAD **barely moves** — outliers are few and RF/MLP already down-weight them.
- H2b: **LR may improve slightly** (a global linear fit is the most outlier-sensitive); RF/MLP unchanged.
- H2c: hard test galaxies stay bad regardless (intrinsic).

**Decision tree:**
- Normal σ_MAD **improves** when O removed → outliers are **harmful training noise** → for production use
  **sample weighting by 1/err²** or trimming (cleaner than hard deletion).
- **No improvement** → outliers are benign in training → don't bother removing; spend effort elsewhere.
- Hard galaxies bad regardless → confirms they need **external info (images)** or a flag/cut.

---

## Experiment 3 — distribution of all 55 columns, hard vs full
**Goal:** find *what separates* the hard set across **every** parquet column — especially columns **not used
in training** (errors, extinction, sizes, position, spectro) — to surface new features, quality flags,
label problems, or instrumental artifacts.

**Method:** for each of the 55 numeric columns compute hard-vs-normal **standardized mean difference**
(effect size) + **KS statistic**; rank by **effect size** (with N this large, ignore p-values).
Group: photometry / **errors** / sizes / extinction / **position·run·field** / **spectro (zErr)**.
Plot distributions for the top discriminators.

**Predictions:**
- H3a (partly confirmed): top discriminators = faint magnitude + **high `*Err`**.
- H3b: extinction, ra/dec, run/field should **not** discriminate (if they do → H-instrument).
- H3c: if **`zErr`** discriminates strongly → **H-label**: some "outliers" are bad ground truth, not model error.

**Decision tree:**
- `*Err` on top → H-noise confirmed → trigger Exp 2's weighting variant + consider an S/N cut.
- An **unused** column discriminates strongly and isn't pure noise → candidate new feature → add it, re-measure outliers.
- run/camcol/field/ra/dec stand out → H-instrument → inspect those runs/fields → data-quality cut.
- `zErr` stands out → H-label → **re-examine the metric**: down-weight / exclude high-`zErr` from evaluation
  (else we punish the model with bad truth; σ_MAD would "improve" artificially).

---

## Cross-experiment decision matrix
| Dominant evidence | Conclusion | Next step |
|---|---|---|
| `*Err`↑ + faint (Exp 3) & weighting helps (Exp 2) | **H-noise** | error-aware model + S/N cut; **temper image-branch hopes** (faint image = weak too) |
| outliers at bright end + `*Err` normal | **H-degeneracy** | **image branch** — this is the CNN's battleground |
| `zErr`↑ | **H-label** | weight/exclude by label quality; σ_MAD will drop "for free" |
| run/field anomalies | **H-instrument** | data-quality cut, revisit freeze |

> Most likely outcome: **mostly H-noise + a minority H-degeneracy** — most are too faint to save (images weak
> there too), a small bright-but-degenerate subset is the real target for the image branch. Deliverable:
> a clean statement of the **tabular ceiling (σ_MAD ≈ 0.014)** + a decomposition of the residual outliers.

## Suggested order & practical notes
1. Finish the running 5-fold, **with metrics + Δz histograms folded in** (= Exp 1 complete).
2. Exp 3 (read-only + plots: fastest, highest info-per-minute) — do next.
3. Exp 2 (retraining: heaviest) — last.
4. Swap RF → `HistGradientBoostingRegressor` everywhere (5–10× faster, comparable accuracy) or 5-fold stays painful.
