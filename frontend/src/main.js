// Wires the input panel to the API + 3D scene: tabular fields, the predict form,
// and the distance-measure selector. Guide: notebooks/tasks-2026-6-19/task-05-ui-wiring.md
import './style.css'
import { createScene } from './scene.js'
import { predict, explain, getHealth } from './api.js'
import { loadSamples, fetchNpy } from './samples.js'
import { DISTANCE_MODES } from './cosmology.js'
import { npyToTexture } from './galaxyImage.js'
import { showGradcam } from './gradcam.js'

// Build a galaxy-image texture from the cutout bytes; null if it can't be decoded
// (addGalaxy then falls back to a coloured sphere).
const textureFor = (buf) => { try { return npyToTexture(buf) } catch { return null } }

const $ = (s) => document.querySelector(s)
const log = (m) => { $('#status').textContent = m }

const viz = createScene($('#scene'), $('#scalebar'))

// the 11 raw catalog fields: [key, example, sliderMin, sliderMax, step]
const TAB_FIELDS = [
  ['dered_u', 19.2, 14, 25, 0.01], ['dered_g', 18.1, 14, 24, 0.01], ['dered_r', 17.4, 13, 23, 0.01],
  ['dered_i', 17.1, 13, 23, 0.01], ['dered_z', 16.9, 13, 23, 0.01],
  ['expRad_r', 3.2, 0, 20, 0.1], ['deVRad_r', 3.6, 0, 20, 0.1], ['petroRad_r', 4.8, 0, 25, 0.1],
  ['petroR50_r', 2.8, 0, 15, 0.1], ['petroR90_r', 7.6, 0, 30, 0.1], ['fracDeV_r', 0.6, 0, 1, 0.01],
]

// task-05a: per field = an "absent" checkbox + a number input + a slider (number <-> slider linked).
// Ticking "absent" marks the feature as missing (greys the row; readTabular omits it so the backend's
// presence mask treats it as absent — the fusion model is trained to run with any subset of features).
function buildTabularInputs() {
  $('#tabular').innerHTML = TAB_FIELDS.map(([k, v, min, max, step]) => `
    <div class="tabrow">
      <label class="tabhead">
        <input type="checkbox" class="abs" /><span class="abs-x">absent</span>
        <span class="tabname">${k}</span>
      </label>
      <div class="tabctl">
        <input class="tabnum" data-tab="${k}" type="number" min="${min}" max="${max}" step="${step}" value="${v}" />
        <input class="tabrange" type="range" min="${min}" max="${max}" step="${step}" value="${v}" />
      </div>
    </div>`).join('')
  $('#tabular').querySelectorAll('.tabrow').forEach(row => {
    const num = row.querySelector('.tabnum'), rng = row.querySelector('.tabrange'), abs = row.querySelector('.abs')
    num.addEventListener('input', () => { rng.value = num.value })
    rng.addEventListener('input', () => { num.value = rng.value })
    abs.addEventListener('change', () => {
      row.classList.toggle('absent', abs.checked)
      num.disabled = rng.disabled = abs.checked
    })
  })
  // master toggle: only show + send tabular (→ fusion) when checked; else image-only (CNN+MDN)
  $('#use-tabular').addEventListener('change', (e) => {
    const on = e.target.checked
    $('#tabular').hidden = !on; $('#tab-json-box').hidden = !on
  })

  // paste-JSON -> fill: set each field from the JSON; fields not present are marked absent.
  $('#tab-json-apply').addEventListener('click', () => {
    const raw = $('#tab-json').value.trim()
    let obj
    try { obj = JSON.parse(raw) }
    catch {                                                    // tolerate Python-dict single quotes
      try { obj = JSON.parse(raw.replace(/'/g, '"')) }
      catch (err) { return log(`bad JSON: ${err.message}`) }
    }
    if (!obj || typeof obj !== 'object') return log('JSON must be an object of { field: value }')
    // each raw field can arrive as itself, OR as the engineered log_<field> (log1p) -> invert via expm1
    const valFor = (k) => {
      if (obj[k] != null && isFinite(obj[k])) return +obj[k]
      const lk = 'log_' + k
      if (obj[lk] != null && isFinite(obj[lk])) return Math.expm1(+obj[lk])
      return null
    }
    let filled = 0
    document.querySelectorAll('#tabular .tabrow').forEach(row => {
      const num = row.querySelector('.tabnum'), rng = row.querySelector('.tabrange'), abs = row.querySelector('.abs')
      const v = valFor(num.dataset.tab)
      const present = v !== null
      abs.checked = !present
      row.classList.toggle('absent', !present)
      num.disabled = rng.disabled = !present
      if (present) { const r = +v.toFixed(4); num.value = r; rng.value = r; filled++ }  // rng clamps to [min,max]
    })
    if (obj.ra != null && isFinite(obj.ra)) $('#ra').value = obj.ra     // bonus: also fill RA/Dec if present
    if (obj.dec != null && isFinite(obj.dec)) $('#dec').value = obj.dec
    log(`filled ${filled} tabular field${filled === 1 ? '' : 's'} from JSON${filled < TAB_FIELDS.length ? ` (${TAB_FIELDS.length - filled} marked absent)` : ''}`)
  })
}

// task-05b: tabular dict for the request — null unless the master "Add tabular features" is on.
// When on, read non-absent fields ({ field: number }); absent/empty ones are omitted (presence mask).
function readTabular() {
  if (!$('#use-tabular')?.checked) return null      // master off -> image-only path on the backend
  const t = {}
  document.querySelectorAll('#tabular .tabrow').forEach(row => {
    const abs = row.querySelector('.abs'), num = row.querySelector('.tabnum')
    if (!abs.checked && num.value !== '') t[num.dataset.tab] = parseFloat(num.value)
  })
  return Object.keys(t).length ? t : null
}

// --- given: backend health badge ---
getHealth()
  .then((h) => { $('#health').textContent = `backend: ${h.status} · ${h.tabular_stack || h.tabular_model || ''}`; $('#health').classList.add('ok') })
  .catch((e) => { $('#health').textContent = `backend: offline (${e.message})` })

// --- given helper ---
function addResultRow({ name, z, distance_gly }) {
  const li = document.createElement('li')
  li.innerHTML = `<b>${name}</b><span>z=${z.toFixed(3)} · ${distance_gly.toFixed(2)} Gly</span>`
  $('#results').prepend(li)
}

// --- given: explore the bundled samples (reference for calling predict + addGalaxy) ---
async function exploreSamples() {
  viz.clear(); $('#results').innerHTML = ''
  const samples = await loadSamples()
  log(`predicting ${samples.length} galaxies…`)
  for (const s of samples) {
    const buf = await fetchNpy(s.npy)
    const res = await predict(buf, { ra: s.ra, dec: s.dec, tabular: s.tabular })
    viz.addGalaxy({ ra: s.ra, dec: s.dec, z: res.z, name: s.name, texture: textureFor(buf) })
    addResultRow({ name: s.name, ...res })
  }
  log(`done — ${samples.length} galaxies. Drag to orbit, scroll to zoom.`)
}
$('#explore').addEventListener('click', () => {
  $('#explore').disabled = true
  exploreSamples().catch((e) => log(`error: ${e.message}`)).finally(() => { $('#explore').disabled = false })
})

// --- auto-orbit: center on the observer and slowly spin; any drag/pan/zoom stops it ---
const orbitBtn = $('#auto-orbit')
const setOrbitUI = (on) => {
  orbitBtn.classList.toggle('active', on)
  orbitBtn.textContent = on ? '⏸ Stop orbit' : '⟳ Auto-orbit'
}
viz.onAutoOrbitEnd(() => setOrbitUI(false))   // a user interaction in the viewport interrupted it
orbitBtn.addEventListener('click', () => {
  if (viz.isAutoOrbit()) { viz.stopAutoOrbit(); setOrbitUI(false) }
  else { viz.startAutoOrbit(); setOrbitUI(true) }
})

// task-05c: predict the user's own .npy cutout (+ optional ra/dec/tabular).
$('#predict-form').addEventListener('submit', async (e) => {
  e.preventDefault()
  const f = $('#file').files[0];  if (!f) return log('choose a .npy first')
  const ra = parseFloat($('#ra').value), dec = parseFloat($('#dec').value)
  log(`predicting ${f.name}…`)
  try {
    const buf = await f.arrayBuffer()
    const res = await predict(buf, { ra, dec, tabular: readTabular() })
    viz.addGalaxy({ ra, dec, z: res.z, name: f.name, texture: textureFor(buf) });  addResultRow({ name: f.name, ...res })
    log(`done — z=${res.z.toFixed(3)} · ${res.distance_gly.toFixed(2)} Gly`)
  } catch (err) { log(`error: ${err.message}`) }
})

// Grad-CAM: explain the chosen .npy cutout — overlay the model's saliency on the galaxy.
$('#explain-btn').addEventListener('click', async () => {
  const f = $('#file').files[0];  if (!f) return log('choose a .npy first')
  $('#explain-btn').disabled = true
  log(`explaining ${f.name}…`)
  try {
    const buf = await f.arrayBuffer()
    const res = await explain(buf, { tabular: readTabular() })
    showGradcam($('#gradcam'), buf, res, f.name)
    log(`Grad-CAM done — ẑ=${res.redshift.toFixed(3)}`)
  } catch (err) { log(`error: ${err.message}`) }
  finally { $('#explain-btn').disabled = false }
})

// task-05d: distance-measure selector -> re-fit the scene with the chosen distance fn.
document.querySelectorAll('input[name="dist"]').forEach(r =>
  r.addEventListener('change', () => viz.setDistanceMode(DISTANCE_MODES[r.value].fn)))

buildTabularInputs()
