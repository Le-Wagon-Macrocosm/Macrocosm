# Fused photo-z backend — task pack (2026-06-17)

We're building the **FastAPI backend** that turns a **64×64×5 ugriz cutout + optional tabular** into a
predicted **redshift**. See **`PLAN.md`** for the contract, dependency graph, waves and owners.

## The idea
The final model **fuses image + tabular** into one prediction (KB *Architecture*). We don't have the
fused CNN yet, so the backend is a **placeholder behind the real contract**:
- **tabular** branch = the **real** trained `baseline_stack.pkl` (16 engineered features),
- **image** branch = a **fake** random-z model (same `.predict` interface the CNN will have).

When the fused CNN artifact is trained it **replaces the model with zero API change**.

Both pickles live in **GCS** (not git): `gs://macrocosm-lewagon/models/{baseline_stack,fake_image_model}.pkl`.
The task notebooks' **Setup cell pulls what they need**; manual: `bash scripts/get_models.sh [--baseline]`.

The backend lives in `backend/` as **skeletons with `# TODO`s**. Each task fills in one piece.

## Workflow (per task)
1. `git checkout 2026.6.17 && git pull origin 2026.6.17`
2. Open your task's `task.ipynb`; **run the Setup cell first** (hops to repo root, pulls models).
3. Develop + test in the *Develop & test here first* cell until the asserts pass — **write it, don't paste**.
4. **Move the working code into the matching `backend/*.py`** (replace the `# TODO`).
5. Run the **Check** cell — it imports from `backend/` and verifies your piece.
6. Run the last cell — it pushes your own branch `task/<folder>`.
7. **Merge back into `2026.6.17`** — follow `MERGE.md` in your task folder.

## Run the whole API (any time pieces are in place)
```bash
bash scripts/get_models.sh --baseline      # pull both models from GCS (real baseline is 657MB)
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# GET localhost:8000/  and POST a .npy cutout (+ ra/dec, optional tabular) to /predict
```

## Conventions
- Don't touch `backend/fake_model.py` or the pickles — provided fixtures.
- Shared files: **02+03** → `features.py`, **06+09** → `model.py`, **07+10** → `main.py`. Each task is its
  own branch + PR; keep **both** sides on a conflict (see `MERGE.md`).
- The real fused model later just needs to serve `predict(image, tabular) -> z`; the API doesn't change.
