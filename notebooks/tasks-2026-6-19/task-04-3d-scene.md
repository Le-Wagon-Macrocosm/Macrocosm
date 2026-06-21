# Task 04 — 3D scene (`src/scene.js`)

The biggest task. The Three.js setup (renderer, camera, OrbitControls, starfield, observer,
render loop) and the public API (`addGalaxy`, `setDistanceMode`, `clear`) are **given**.
Implement the four marked functions. **Depends on Task 02** (`comovingGly` is imported).

Given helpers you'll use: `zColor(z)`, `niceBelow(v)` (round 1/2/5×10ᵏ), `fmtGly(g)`, and the
state vars `items` (`{ra,dec,z,name,mesh}[]`), `distanceFn`, `glyPerUnit`, groups `galaxies`/`rings`.

## 04a — `dirFromRaDec(ra, dec)` → `THREE.Vector3`
Unit vector for a sky direction (degrees → radians with `DEG`):
```
x = cos(dec)·cos(ra),  y = sin(dec),  z = cos(dec)·sin(ra)
```

## 04b — `placeAll()`  (the core)
Position every item and auto-fit the scene:
```
if items empty: rings.clear(); return
dists  = items.map(it => distanceFn(it.z))     // Gly
maxGly = max(dists)
glyPerUnit = maxGly / FIT_RADIUS               // farthest galaxy -> FIT_RADIUS scene units
for each it,i: it.mesh.position = dirFromRaDec(it.ra,it.dec).multiplyScalar(dists[i]/glyPerUnit)
rebuildRings(maxGly)
```
`placeAll()` is already called by `addGalaxy` and `setDistanceMode`, so switching distance mode
re-fits automatically.

## 04c — `rebuildRings(maxGly)`
Faint distance rings centered on the observer, in the XZ plane:
```
rings.clear()
step = niceBelow(maxGly/3) || 1
for g = step; g <= maxGly*1.001; g += step:
  r = g / glyPerUnit                                   // scene units
  mesh = new THREE.Mesh(new THREE.RingGeometry(r-0.02, r+0.02, 96),
            new THREE.MeshBasicMaterial({ color: 0x2a3160, side: THREE.DoubleSide }))
  mesh.rotation.x = Math.PI/2;  rings.add(mesh)
```

## 04d — `updateScaleBar()`  (dynamic scale bar)
Runs every frame (loop already calls it, wrapped in try/catch). Set the HUD bar width + label:
```
if (!scaleBarEl) return
camDist    = camera.position.distanceTo(controls.target)
worldPerPx = 2*Math.tan((camera.fov/2)*DEG)*camDist / canvas.clientHeight
glyPerPx   = worldPerPx * glyPerUnit
nice       = niceBelow(130 * glyPerPx)                 // aim ~130px wide
scaleBarEl.style.width = (nice/glyPerPx) + 'px'
scaleBarEl.firstElementChild.textContent = fmtGly(nice)
```

## Test
Hard to unit-test alone; verify visually once Task 05 wires the UI (or temporarily call
`viz.addGalaxy({ra:180,dec:0,z:0.2,name:'t'})` from the console). You should see:
spheres placed at a distance (colored by z), faint rings, and a scale bar that grows/shrinks as
you zoom and changes when you switch distance mode.
