# tasks-2026-6-19 — Frontend task pack (Three.js photo-z 3D explorer)

Build the **static** frontend that lets you predict a galaxy's redshift from a ugriz cutout
(+ optional tabular features) and place galaxies in a 3D scene by their distance. Vite +
Three.js, deployed to **GitHub Pages** (no server — the browser calls the Cloud Run backend).

Live backend: `https://macrocosm-backend-4cqy5oe74a-ew.a.run.app` (`/docs` for the API).

## Setup (once)
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 — hot reload while you work
```
The scaffolding (HTML/CSS, Vite config, sample cutouts, `config.js`) is **done**. You implement
the 5 JS modules below — each is one file, so no merge conflicts.

## Tasks (one file each)
| Task | File | What |
|------|------|------|
| [01 api-client](task-01-api-client.md)   | `src/api.js`       | `getHealth()` + `predict()` — the backend contract |
| [02 cosmology](task-02-cosmology.md)     | `src/cosmology.js` | z → comoving / light-travel / luminosity distance |
| [03 samples](task-03-samples.md)         | `src/samples.js`   | load the bundled demo galaxies |
| [04 3d-scene](task-04-3d-scene.md)       | `src/scene.js`     | place galaxies in 3D + reference rings + dynamic scale bar |
| [05 ui-wiring](task-05-ui-wiring.md)     | `src/main.js`      | tabular inputs, predict form, distance-mode selector |

## Order / dependencies
- **01, 02, 03 are independent** — start in parallel.
- **04** needs **02** (it calls `comovingGly` to place galaxies).
- **05** needs **01 + 03 + 04** (it calls `predict`, `loadSamples`, `viz.addGalaxy`).

Suggested: 01·02·03 first (3 people), then 04, then 05. The app runs at every step — finished
modules work, unfinished ones show a `TODO task-xx` error in the status line / console.

## How to know you're done
Run `npm run dev`, click **"Explore sample galaxies"**: 8 galaxies appear in 3D, colored by
redshift, spread by distance. Toggle the distance mode (top-left) — they re-place; the scale
bar (bottom-left) updates as you zoom. Upload your own `.npy` + fill tabular → a real prediction.

## Don't
- Don't change `src/config.js`, `index.html`, `src/style.css`, or `public/samples/` (given).
- Don't add a Node/Express server — it's static. Keep it building with `npm run build`.
