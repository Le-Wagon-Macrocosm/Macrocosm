# Task 02 — cosmology (`src/cosmology.js`)

Convert a redshift `z` into three distance measures, so the viewer can switch how galaxies
are placed. **No deps on other tasks.** Flat Planck18 constants are given (`H0`, `OM`, `OL`,
`D_H` = Hubble distance in Gly, and `E(z)`).

## The physics (all in Gly)
With `E(z) = sqrt(OM·(1+z)³ + OL)`:
- **Comoving**:     `D_C(z)  = D_H · ∫₀ᶻ dz'/E(z')`
- **Light-travel**: `D_LT(z) = D_H · ∫₀ᶻ dz'/((1+z')·E(z'))`
- **Luminosity**:   `D_L(z)  = (1+z) · D_C(z)`   (flat universe)

For small z all three ≈ `D_H·z`; they diverge as z grows (`D_LT < D_C < D_L`).

## Implement
**`integrate(f, z, n=512)`** — numeric integral of `f` from 0 to z. Trapezoidal is plenty:
```
if (z <= 0) return 0
h = z/n;  s = 0.5*(f(0)+f(z));  for i in 1..n-1: s += f(i*h);  return s*h
```
Then:
- `comovingGly  = (z) => D_H * integrate(zz => 1/E(zz), z)`
- `lightTravelGly = (z) => D_H * integrate(zz => 1/((1+zz)*E(zz)), z)`
- `luminosityGly = (z) => (1+z) * comovingGly(z)`

> Keep `DISTANCE_MODES` keys (`comoving`, `lightTravel`, `luminosity`) unchanged — the UI uses them.

## Test
```js
const c = await import('/src/cosmology.js')
[0.05, 0.2, 0.35].forEach(z =>
  console.log(z, c.lightTravelGly(z).toFixed(2), c.comovingGly(z).toFixed(2), c.luminosityGly(z).toFixed(2)))
// expect roughly:  0.2 -> 2.51  2.75  3.30   (LT < CM < LUM, and CM matches the backend's distance_gly)
```
