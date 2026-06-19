# Merge your work back into `2026.6.17`

You pushed branch **`task/02-features-tabular`**. Get it into `2026.6.17`:

## Option A — Pull Request (preferred)
On GitHub: **base = `2026.6.17`**, **compare = `task/02-features-tabular`** → create + merge the PR.

## Option B — command line
```bash
git checkout 2026.6.17 && git pull origin 2026.6.17
git merge task/02-features-tabular
git push origin 2026.6.17
```

## If it conflicts
`02+03` share `features.py`, `06+09` share `model.py`, `07+10` share `main.py`. Pull in others' work
on **your** branch and keep **both** sides:
```bash
git checkout task/02-features-tabular
git merge origin/2026.6.17    # keep BOTH functions/routes; delete the <<< === >>> markers
git add <file> && git commit && git push origin task/02-features-tabular
```
> Never delete a teammate's function/route to "resolve" a conflict — keep both.
