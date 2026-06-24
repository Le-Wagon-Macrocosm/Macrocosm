# Merge your work back into `2026.6.17`

You pushed branch **`task/cnn-03-build-embedder`**.

## PR (preferred)
GitHub: **base = `2026.6.17`**, compare = `task/cnn-03-build-embedder` → create + merge.

## CLI
```bash
git checkout 2026.6.17 && git pull origin 2026.6.17
git merge task/cnn-03-build-embedder
git push origin 2026.6.17
```

## Conflict
All three CNN tasks edit `cnn/model.py`. Pull others' work on YOUR branch and keep **all** functions:
```bash
git checkout task/cnn-03-build-embedder
git merge origin/2026.6.17     # keep every function; delete the <<< === >>> markers
git add cnn/model.py && git commit && git push origin task/cnn-03-build-embedder
```
> Never delete a teammate's function to resolve a conflict — keep all three.
