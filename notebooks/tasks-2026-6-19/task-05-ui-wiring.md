# Task 05 — UI wiring (`src/main.js`)

Connect the input panel to the API + scene. **Depends on 01 (`predict`), 03 (`loadSamples`),
04 (`viz.addGalaxy`/`setDistanceMode`).** The "Explore samples" flow, the health badge, and
`addResultRow` are **given** — use `exploreSamples()` as your reference for calling the API and
adding to the scene.

Relevant markup in `index.html` (already there): `#predict-form`, `#file`, `#ra`, `#dec`,
`#tabular`, `input[name="dist"]` radios, `#status`, `#results`. `TAB_FIELDS` (the 11 fields +
example values) is given.

## 05a — `buildTabularInputs()`
Inject one input per field into `#tabular`:
```js
$('#tabular').innerHTML = TAB_FIELDS.map(([k, v]) =>
  `<label>${k}<input data-tab="${k}" type="number" step="any" value="${v}" /></label>`).join('')
```

## 05b — `readTabular()`
Collect the filled inputs into `{ field: number }`; skip empty ones; return `null` if none:
```js
const t = {}
document.querySelectorAll('[data-tab]').forEach(el => { if (el.value !== '') t[el.dataset.tab] = parseFloat(el.value) })
return Object.keys(t).length ? t : null
```

## 05c — predict form submit
```js
$('#predict-form').addEventListener('submit', async (e) => {
  e.preventDefault()
  const f = $('#file').files[0];  if (!f) return log('choose a .npy first')
  const ra = parseFloat($('#ra').value), dec = parseFloat($('#dec').value)
  log(`predicting ${f.name}…`)
  try {
    const res = await predict(await f.arrayBuffer(), { ra, dec, tabular: readTabular() })
    viz.addGalaxy({ ra, dec, z: res.z, name: f.name });  addResultRow({ name: f.name, ...res })
    log(`done — z=${res.z.toFixed(3)} · ${res.distance_gly.toFixed(2)} Gly`)
  } catch (err) { log(`error: ${err.message}`) }
})
```

## 05d — distance-mode selector
```js
document.querySelectorAll('input[name="dist"]').forEach(r =>
  r.addEventListener('change', () => viz.setDistanceMode(DISTANCE_MODES[r.value].fn)))
```

## Test
`npm run dev` → the tabular fields render; **Explore** places 8 galaxies; switching Comoving↔
Luminosity re-spreads them; uploading a `.npy` (+ optional tabular) adds one. No console errors.
