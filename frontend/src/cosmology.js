// TASK 02 — convert redshift z to distances (flat Planck18). Implement the three
// distance functions so the distance-mode selector works.
// Guide: notebooks/tasks-2026-6-19/task-02-cosmology.md
const H0 = 67.66          // km/s/Mpc
const OM = 0.30966        // matter density
const OL = 1 - OM         // flat universe -> dark energy
const C_KM_S = 299792.458
const MPC_TO_GLY = 3.26156e-3
const D_H = (C_KM_S / H0) * MPC_TO_GLY    // Hubble distance, ~14.45 Gly  (given)

// Dimensionless expansion rate E(z) = sqrt(Om(1+z)^3 + OL)   (given)
const E = (z) => Math.sqrt(OM * (1 + z) ** 3 + OL)

// TODO: numerically integrate f from 0 to z (e.g. trapezoidal, n~512 steps).
//       Return 0 when z <= 0.
function integrate(f, z, n = 512) {
  if (z <= 0) return 0

  const h = z / n
  let s = 0.5 * (f(0) + f(z))

  for (let i = 1; i < n, i++) {
    s += f(i * h)
  }

  return s * h
}

// TODO: comoving distance  = D_H * ∫_0^z dz'/E(z')
export const comovingGly = (z) => {
  return D_H * integrate((zz) => 1 / E(zz), z)
}

// TODO: light-travel dist  = D_H * ∫_0^z dz'/((1+z')·E(z'))
export const lightTravelGly = (z) => {
  return D_H * integrate((zz) => 1 / E(1+zz) * E(zz), z)
}

// TODO: luminosity distance = (1+z) * comoving distance   (flat universe)
export const luminosityGly = (z) => {
  return (1 + z) * comovingGly(z)
}

// Used by the distance-mode selector (do not rename the keys).
export const DISTANCE_MODES = {
  comoving:    { label: 'Comoving',     fn: comovingGly },
  lightTravel: { label: 'Light-travel', fn: lightTravelGly },
  luminosity:  { label: 'Luminosity',   fn: luminosityGly },
}
