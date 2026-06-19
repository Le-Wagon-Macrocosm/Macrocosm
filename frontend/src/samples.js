// TASK 03 — load the bundled demo galaxies from public/samples/.
// import.meta.env.BASE_URL makes paths work at the domain root AND under a
// GitHub Pages /<repo>/ path. Guide: notebooks/tasks-2026-6-19/task-03-samples.md
const BASE = import.meta.env.BASE_URL

export async function loadSamples() {
  // TODO: fetch `${BASE}samples/manifest.json`, throw if !res.ok, return res.json()
  //       (an array of { id, name, npy, ra, dec, tabular }).
  throw new Error('TODO task-03: implement loadSamples()')
}

export async function fetchNpy(path) {
  // TODO: fetch `${BASE}${path}`, throw if !res.ok, return res.arrayBuffer().
  throw new Error('TODO task-03: implement fetchNpy()')
}
