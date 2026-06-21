// Wires the input panel to the API + 3D scene: tabular fields, the predict form,
// and the distance-measure selector. Guide: notebooks/tasks-2026-6-19/task-05-ui-wiring.md
import './style.css'
import { createScene } from './scene.js'
import { predict, getHealth } from './api.js'
import { loadSamples, fetchNpy } from './samples.js'
import { DISTANCE_MODES } from './cosmology.js'

const $ = (s) => document.querySelector(s)
const log = (m) => { $('#status').textContent = m }

const viz = createScene($('#scene'), $('#scalebar'))

// the 11 raw catalog fields + example values
const TAB_FIELDS = [
  ['dered_u', 19.2], ['dered_g', 18.1], ['dered_r', 17.4], ['dered_i', 17.1], ['dered_z', 16.9],
  ['expRad_r', 3.2], ['deVRad_r', 3.6], ['petroRad_r', 4.8], ['petroR50_r', 2.8],
  ['petroR90_r', 7.6], ['fracDeV_r', 0.6],
]

// task-05a: inject one number input per field into #tabular (prefilled with the example).
function buildTabularInputs() {
  $('#tabular').innerHTML = TAB_FIELDS.map(([k, v]) =>
  `<label>${k}<input data-tab="${k}" type="number" step="any" value="${v}" /></label>`).join('')
}

// task-05b: read the filled tabular inputs into { field: number } (null if none).
function readTabular() {
  const t = {}
  document.querySelectorAll('[data-tab]').forEach(el => { if (el.value !== '') t[el.dataset.tab] = parseFloat(el.value) })
  return Object.keys(t).length ? t : null
}

// --- given: backend health badge ---
getHealth()
  .then((h) => { $('#health').textContent = `backend: ${h.status} · ${h.tabular_model}`; $('#health').classList.add('ok') })
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
    const res = await predict(await fetchNpy(s.npy), { ra: s.ra, dec: s.dec, tabular: s.tabular })
    viz.addGalaxy({ ra: s.ra, dec: s.dec, z: res.z, name: s.name })
    addResultRow({ name: s.name, ...res })
  }
  log(`done — ${samples.length} galaxies. Drag to orbit, scroll to zoom.`)
}
$('#explore').addEventListener('click', () => {
  $('#explore').disabled = true
  exploreSamples().catch((e) => log(`error: ${e.message}`)).finally(() => { $('#explore').disabled = false })
})

// task-05c: predict the user's own .npy cutout (+ optional ra/dec/tabular).
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

// task-05d: distance-measure selector -> re-fit the scene with the chosen distance fn.
document.querySelectorAll('input[name="dist"]').forEach(r =>
  r.addEventListener('change', () => viz.setDistanceMode(DISTANCE_MODES[r.value].fn)))

buildTabularInputs()
