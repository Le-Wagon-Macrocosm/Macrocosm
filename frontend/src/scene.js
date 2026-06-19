// TASK 04 — the 3D explorer. The Three.js boilerplate is given; implement the four
// TODO functions (direction from ra/dec, placing+fitting galaxies, reference rings,
// dynamic scale bar). Guide: notebooks/tasks-2026-6-19/task-04-3d-scene.md
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { comovingGly } from './cosmology.js'

const DEG = Math.PI / 180
const FIT_RADIUS = 16 // the farthest galaxy is placed at this many scene units

// --- given helpers ---
function zColor(z) {
  const t = THREE.MathUtils.clamp(z / 0.4, 0, 1)
  return new THREE.Color().setHSL((1 - t) * 0.66, 0.85, 0.55)
}
function niceBelow(v) {                  // 1/2/5 x10^k just below v
  if (v <= 0) return 1
  const p = Math.pow(10, Math.floor(Math.log10(v))), m = v / p
  return (m >= 5 ? 5 : m >= 2 ? 2 : 1) * p
}
const fmtGly = (g) => (g >= 1 ? `${+g.toFixed(g < 10 ? 1 : 0)} Gly` : `${Math.round(g * 1000)} Mly`)

export function createScene(canvas, scaleBarEl) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0x05060f)
  const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 5000)
  camera.position.set(0, 10, 30)
  const controls = new OrbitControls(camera, canvas)
  controls.enableDamping = true

  // starfield + observer at the origin (given)
  const starPos = new Float32Array(1800 * 3)
  for (let i = 0; i < starPos.length; i++) starPos[i] = (Math.random() - 0.5) * 600
  const starGeo = new THREE.BufferGeometry()
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3))
  scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0x8888aa, size: 0.6 })))
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(0.35, 16, 16), new THREE.MeshBasicMaterial({ color: 0xffcc33 })))
  const galaxies = new THREE.Group(); scene.add(galaxies)
  const rings = new THREE.Group(); scene.add(rings)

  let items = []                 // { ra, dec, z, name, mesh }
  let distanceFn = comovingGly
  let glyPerUnit = 1             // 1 scene unit == glyPerUnit Gly (set by placeAll)

  // TODO task-04a: unit vector pointing at (ra[deg], dec[deg]).
  //   x = cos(dec)cos(ra), y = sin(dec), z = cos(dec)sin(ra)   (deg -> rad with DEG)
  function dirFromRaDec(ra, dec) {
    throw new Error('TODO task-04a: dirFromRaDec')
  }

  // TODO task-04b: position every item.
  //   dists = items.map(it => distanceFn(it.z)); maxGly = max(dists)
  //   glyPerUnit = maxGly / FIT_RADIUS         // auto-fit so farthest sits at FIT_RADIUS
  //   each mesh.position = dirFromRaDec(ra,dec) * (dist / glyPerUnit)
  //   then call rebuildRings(maxGly). Handle the empty list (clear rings, return).
  function placeAll() {
    throw new Error('TODO task-04b: placeAll')
  }

  // TODO task-04c: faint reference rings (in the XZ plane) at round distances.
  //   step = niceBelow(maxGly/3); for g = step; g <= maxGly; g += step:
  //     ring radius (scene units) = g / glyPerUnit; add a thin THREE.RingGeometry mesh
  //     (rotate.x = PI/2). Clear `rings` first.
  function rebuildRings(maxGly) {
    throw new Error('TODO task-04c: rebuildRings')
  }

  // TODO task-04d: dynamic scale bar (set scaleBarEl width + label).
  //   camDist = camera.position.distanceTo(controls.target)
  //   worldPerPx = 2*tan(fov/2 in rad)*camDist / canvas.clientHeight
  //   glyPerPx = worldPerPx * glyPerUnit
  //   nice = niceBelow(130 * glyPerPx)               // ~130px target
  //   scaleBarEl.style.width = (nice/glyPerPx)+'px'; firstElementChild.textContent = fmtGly(nice)
  function updateScaleBar() {
    if (!scaleBarEl) return
    // (leave as no-op until implemented; the render loop tolerates it)
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix()
  }
  window.addEventListener('resize', resize); resize()

  ;(function loop() {
    requestAnimationFrame(loop)
    controls.update()
    try { updateScaleBar() } catch (_) { /* until task-04d */ }
    renderer.render(scene, camera)
  })()

  return {
    addGalaxy({ ra, dec, z, name }) {
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(0.4, 20, 20), new THREE.MeshBasicMaterial({ color: zColor(z) }))
      mesh.userData = { name, z }
      galaxies.add(mesh)
      items.push({ ra, dec, z, name, mesh })
      placeAll()
      controls.target.lerp(mesh.position, 0.2)
    },
    setDistanceMode(fn) { distanceFn = fn; placeAll() },
    clear() { galaxies.clear(); rings.clear(); items = []; controls.target.set(0, 0, 0) },
  }
}
