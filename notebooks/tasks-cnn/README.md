# CNN architecture — task pack

Build the photo-z image-branch CNN in **`cnn/model.py`**, in 3 steps. Pure Keras — **no GCS, no GPU,
no real data**; everything unit-tests on CPU with synthetic tensors. See `PLAN.md` for the chain.

## Workflow (per task)
1. `git fetch origin && git checkout 2026.6.17 && git pull origin 2026.6.17`
2. Open your task's `task.ipynb`, **run the Setup cell first** (hops to repo root, imports tensorflow).
3. Fill the *Develop & test here first* cell until the asserts pass — **write it, don't paste**.
4. **Move the working function into `cnn/model.py`** (replace the `# TODO`).
5. Run the **Check** cell — it imports from `cnn/` and verifies your piece.
6. Run the last cell — it pushes your own branch `task/cnn-<folder>`; then merge via `MERGE.md`.

## Conventions
- The 3 tasks are a **chain** (02 uses 01, 03 uses 02) and all edit `cnn/model.py` — do them in order;
  keep all functions on a merge conflict.
- Need `tensorflow` installed locally (Colab has it; or the team `lewagon` env).
- The architecture is already decided (KB MCM-A-18); these tasks implement it, not redesign it.
