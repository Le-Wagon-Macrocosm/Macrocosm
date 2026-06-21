// TASK 03 — load the bundled demo galaxies from public/samples/.
// import.meta.env.BASE_URL makes paths work at the domain root AND under a
// GitHub Pages /<repo>/ path. Guide: notebooks/tasks-2026-6-19/task-03-samples.md
const BASE = import.meta.env.BASE_URL

export async function loadSamples() {
  // fetch `${BASE}samples/manifest.json`, throw if !res.ok, return res.json()
  //       (an array of { id, name, npy, ra, dec, tabular }).
  const res = await fetch(`${BASE}samples/manifest.json`);
  if (!res.ok) {
    throw new Error(`Failed to fetch manifest: ${res.status} ${res.statusText}`);
  }
  return res.json()
}

export async function fetchNpy(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.status} ${res.statusText}`)
  }
  return res.arrayBuffer()
}
