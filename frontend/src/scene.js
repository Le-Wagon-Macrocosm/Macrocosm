// The 3D explorer: galaxies placed by (ra,dec) at a z-derived distance, the scene
// auto-fits the farthest to a fixed radius, faint reference rings mark round distances,
// and a dynamic scale bar tracks the Gly-per-screen scale as you zoom.
// Guide: notebooks/tasks-2026-6-19/task-04-3d-scene.md
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

  // task-04a: unit vector pointing at (ra[deg], dec[deg]).
  function dirFromRaDec(ra, dec) {
    const a = ra * DEG, d = dec * DEG
    return new THREE.Vector3(Math.cos(d) * Math.cos(a), Math.sin(d), Math.cos(d) * Math.sin(a))
  }

  // task-04b: position every item and auto-fit so the farthest sits at FIT_RADIUS.
  function placeAll() {
    if (!items.length) { rings.clear(); return }
    const dists = items.map((it) => distanceFn(it.z))
    const maxGly = Math.max(...dists, 1e-6)
    glyPerUnit = maxGly / FIT_RADIUS
    items.forEach((it, i) =>
      it.mesh.position.copy(dirFromRaDec(it.ra, it.dec).multiplyScalar(dists[i] / glyPerUnit)))
    rebuildRings(maxGly)
  }

  // task-04c: faint reference rings (in the XZ plane) at round distances.
  function rebuildRings(maxGly) {
    rings.clear()
    const step = niceBelow(maxGly / 3) || 1
    for (let g = step; g <= maxGly * 1.001; g += step) {
      const geo = new THREE.RingGeometry(g / glyPerUnit - 0.02, g / glyPerUnit + 0.02, 96)
      const ring = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0x2a3160, side: THREE.DoubleSide }))
      ring.rotation.x = Math.PI / 2
      rings.add(ring)
    }
  }

  // task-04d: dynamic scale bar (set scaleBarEl width + label, ~130px target).
  function updateScaleBar() {
    if (!scaleBarEl) return
    const camDist = camera.position.distanceTo(controls.target)
    const worldPerPx = (2 * Math.tan((camera.fov / 2) * DEG) * camDist) / canvas.clientHeight
    const glyPerPx = worldPerPx * glyPerUnit
    const nice = niceBelow(130 * glyPerPx)
    scaleBarEl.style.width = `${nice / glyPerPx}px`
    scaleBarEl.firstElementChild.textContent = fmtGly(nice)
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
    addGalaxy({ ra, dec, z, name, texture }) {
      // With a cutout texture: a camera-facing billboard of the actual galaxy image,
      // ringed in its z-colour. Without one: fall back to a z-coloured sphere.
      let mesh
      if (texture) {
        mesh = new THREE.Group()
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthWrite: false }))
        sprite.scale.set(1.6, 1.6, 1)
        const halo = new THREE.Sprite(new THREE.SpriteMaterial({
          color: zColor(z), transparent: true, opacity: 0.5, depthWrite: false }))
        halo.scale.set(1.9, 1.9, 1)
        mesh.add(halo, sprite)
      } else {
        mesh = new THREE.Mesh(new THREE.SphereGeometry(0.4, 20, 20), new THREE.MeshBasicMaterial({ color: zColor(z) }))
      }
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
