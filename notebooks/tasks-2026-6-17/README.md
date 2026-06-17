# Image photo-z backend — task pack (2026-06-17)

We're building the **FastAPI backend** that turns a **64×64×5 ugriz image cutout** into a predicted
**redshift**. See **`PLAN.md`** for the dependency graph, waves, and suggested owners.

## The idea
The real model is a CNN we haven't trained yet. So we ship a **placeholder**:
`models/fake_image_model.pkl` — a `RandomRedshiftModel` that takes `(n, 64, 64, 5)` and returns random
z in `[0.02, 0.35]`. It exposes the **same `.predict` interface** the real CNN will, so we can build
and test the *entire* API today and swap the real model in later with zero code change.

The pickle is **not in git** — it lives in GCS (`gs://macrocosm-lewagon/models/fake_image_model.pkl`).
The task notebooks' **Setup cell pulls it automatically**; to fetch it manually run
`bash scripts/get_fake_model.sh` from the repo root (needs gcloud auth — see the main `README.md`).

The backend lives in `backend/` as **skeletons with `# TODO`s**. Each task fills in one piece.

## Workflow (per task)
1. `git checkout 2026.6.17 && git pull origin 2026.6.17`
2. Open your task's `task.ipynb`. **Run the Setup cell first** (it hops to the repo root so `import
   backend` and `models/...` work).
3. Develop + test your function in the notebook until it works on the fake data.
4. **Move the working code into the matching `backend/*.py`** (replace the `# TODO`).
5. Run the **Check** cell — it imports from `backend/` and verifies your piece.
6. Run the last cell — it commits & pushes **your own branch** `task/<folder>` (e.g.
   `task/03-preprocessing`).
7. **Merge your branch back into `2026.6.17`** — follow `MERGE.md` in your task folder (PR or CLI).

## Run the whole API (any time pieces are in place)
```bash
# from the repo root, in the macrocosm venv
bash scripts/get_fake_model.sh        # pull the placeholder model from GCS (once)
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# then:  curl localhost:8000/        and POST a 64x64x5 image to /predict
```

## Conventions
- Don't touch `backend/fake_model.py` or the pickle — they're the provided placeholder model.
- Every task pushes its **own branch** `task/<folder>` and merges via PR — so `04`+`07` (both `model.py`)
  and `05`+`08` (both `main.py`) can't clobber each other. Branch off a fresh `2026.6.17`; if a PR
  conflicts, `git merge origin/2026.6.17` and resolve before merging.
- The real CNN later just needs to expose `.predict((n,64,64,5)) -> (n,)`; nothing else changes.
