# Merge your work back into `2026.6.17`

You pushed your work on branch **`task/01-config`** (the last cell of `task.ipynb` did this).
Now get it into the shared branch **`2026.6.17`**.

## Option A — Pull Request (preferred)
1. On GitHub you'll see a banner for `task/01-config` -> **Compare & pull request**.
2. Set **base = `2026.6.17`**, **compare = `task/01-config`**, create the PR.
3. If GitHub says it can't merge automatically, see **Resolve a conflict** below.
4. Merge the PR. Done.

## Option B — From the command line
```bash
git checkout 2026.6.17
git pull origin 2026.6.17
git merge task/01-config
git push origin 2026.6.17
```

## Resolve a conflict (only if git/GitHub complains)
`04`+`07` both edit `backend/model.py` and `05`+`08` both edit `backend/main.py`, so two tasks can
touch the same file. Bring in everyone else's changes on YOUR branch, keep **both** sides, then push:
```bash
git checkout task/01-config
git merge origin/2026.6.17          # pull in the latest shared branch
# open the conflicted file: keep BOTH functions/routes, delete the <<<<<<< ======= >>>>>>> markers
git add <file>
git commit
git push origin task/01-config            # your PR now merges cleanly
```
> Never delete a teammate's function/route to "fix" a conflict — keep both.
