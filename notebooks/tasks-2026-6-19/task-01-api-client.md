# Task 01 — API client (`src/api.js`)

Implement the two functions that talk to the FastAPI backend. **No deps on other tasks.**

## Background
The backend (`/docs` for live schema) exposes:
- `GET /` → `{ "status": "ok", "tabular_model": "...", "image_model": "...", "input_shape": [64,64,5] }`
- `POST /predict` — **multipart/form-data**:
  - `file` (required): a `.npy` of a `(64,64,5)` float32 ugriz cutout
  - `ra`, `dec` (optional): numbers
  - `tabular` (optional): a JSON **string** of raw catalog fields
  → `{ "z": 0.11, "distance_gly": 1.56, "z_lo": null, "z_hi": null }`

CORS is open, so the browser can call it directly. `API_BASE` is already imported from `config.js`.

## Implement
**`getHealth()`** — `fetch(\`${API_BASE}/\`)`; throw on `!res.ok`; return `res.json()`.

**`predict(npyBytes, { ra, dec, tabular })`**
1. `const fd = new FormData()`
2. `fd.append('file', new Blob([npyBytes], { type: 'application/octet-stream' }), 'cutout.npy')`
3. append `'ra'`/`'dec'` as `String(value)` — **skip** when `null` or `Number.isNaN`
4. append `'tabular'` as `JSON.stringify(tabular)` — **skip** when `null`
5. `fetch(\`${API_BASE}/predict\`, { method: 'POST', body: fd })`
6. on `!res.ok` throw `new Error(\`predict ${res.status}: ${await res.text()}\`)`; else return `res.json()`

> Don't set `Content-Type` yourself — the browser sets the multipart boundary for `FormData`.

## Test
In the browser console (with `npm run dev` running):
```js
const { getHealth, predict } = await import('/src/api.js')
await getHealth()                                  // -> { status: "ok", ... }
const buf = await (await fetch('/samples/sample_00.npy')).arrayBuffer()
await predict(buf, { ra: 180, dec: 0 })            // -> { z, distance_gly, ... }
```
Both return objects with no error. (First `/predict` after idle can take ~10–15s — Cloud Run cold start.)
