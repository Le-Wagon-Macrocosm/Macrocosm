# Task 03 — sample loader (`src/samples.js`)

Load the bundled demo galaxies from `public/samples/`. **No deps on other tasks.** Small task.

## Background
`public/samples/manifest.json` is an array of:
```json
{ "id": 0, "name": "Andromeda-like", "npy": "samples/sample_00.npy",
  "ra": 123.4, "dec": -12.3, "tabular": { "dered_u": 18.0, ... } }
```
`BASE = import.meta.env.BASE_URL` is given — prepend it so paths work both locally and under a
GitHub Pages `/<repo>/` path.

## Implement
- **`loadSamples()`** → `fetch(\`${BASE}samples/manifest.json\`)`; throw on `!res.ok`; return `res.json()`.
- **`fetchNpy(path)`** → `fetch(\`${BASE}${path}\`)`; throw on `!res.ok`; return `res.arrayBuffer()`
  (the raw bytes, to forward to `predict`).

## Test
```js
const s = await import('/src/samples.js')
const m = await s.loadSamples();  console.log(m.length, m[0])      // 8, first sample object
const buf = await s.fetchNpy(m[0].npy);  console.log(buf.byteLength) // ~81920 bytes
```
