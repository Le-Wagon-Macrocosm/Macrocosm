# Tasks — CNN architecture (image branch)

Build the photo-z **image-branch CNN** in `cnn/model.py`: a VGG stem + 3 lightweight Inception
modules + a `GlobalAveragePooling` head that outputs both a standalone **z** prediction and a 64-d
**`embedding`** (the vector the fusion MLP head consumes). ~288K params; size-agnostic via GAP.

> Background: KB *CNN architectures — VGG vs Inception* (MCM-A-18), *Modeling routes*, *Architecture*.

## Tasks (a dependency chain — do in order)
| # | folder | implements | depends on |
|---|---|---|---|
| 01 | `01-inception` | `inception()` — 4-branch multi-scale module | — |
| 02 | `02-build-cnn` | `build_cnn()` — stem + 3 inception + heads | 01 |
| 03 | `03-build-embedder` | `build_embedder()` — 64-d feature extractor for fusion | 02 |

All three live in **`cnn/model.py`** (each pushes its own branch, keep-all on merge — see `MERGE.md`).

## Out of scope (separate packs / later)
- Data loading (`load_set` — KB *Loading the dataset for training*), tf.data + augmentation, the
  training loop + **MLflow** logging, and the **fusion head** (freeze base models + CNN, train the MLP).
- Architecture choices (64 input, VGG+Inception hybrid, embed_dim 64) are already decided — see MCM-A-18.

## Test locally (no GPU / GCS needed)
Every task unit-tests on CPU with synthetic tensors — just `tensorflow` installed. Run the Setup cell,
fill the dev cell until the asserts pass, move into `cnn/model.py`, run Check.
