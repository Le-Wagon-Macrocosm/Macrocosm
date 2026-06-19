// TASK 01 — backend client. Implement getHealth() and predict().
// Guide: notebooks/tasks-2026-6-19/task-01-api-client.md
import { API_BASE } from './config.js'

export async function getHealth() {
  // TODO: GET `${API_BASE}/`, throw if !res.ok, return the parsed JSON
  //       ({ status, tabular_model, image_model, input_shape }).
  const res = await fetch(`${API_BASE}/`)
  if (!res.ok) throw new Error(`health ${res.status}: ${await res.text()}`)
  return res.json()
}

// npyBytes : ArrayBuffer of a (64,64,5) float32 .npy cutout   (required)
// opts     : { ra?:number, dec?:number, tabular?:object }     (all optional)
// returns  : { z, distance_gly, z_lo, z_hi }
export async function predict(npyBytes, { ra = null, dec = null, tabular = null } = {}) {
  // TODO: build a FormData and POST it to `${API_BASE}/predict` (multipart/form-data):
  //   - "file"   : new Blob([npyBytes]) with filename "cutout.npy"
  //   - "ra"/"dec": String(value)  — skip when null or NaN
  //   - "tabular": JSON.stringify(tabular) — skip when null
  // Throw on !res.ok (include res.status + text); otherwise return res.json().
  const fd = new FormData()
  fd.append('file', new Blob([npyBytes], { type: 'application/octet-stream' }), 'cutout.npy')
  if (ra !== null && !Number.isNaN(ra))   fd.append('ra',  String(ra))
  if (dec !== null && !Number.isNaN(dec)) fd.append('dec', String(dec))
  if (tabular !== null)                   fd.append('tabular', JSON.stringify(tabular))
  const res = await fetch(`${API_BASE}/predict`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`predict ${res.status}: ${await res.text()}`)
  return res.json()
}
