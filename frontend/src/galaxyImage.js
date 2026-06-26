// Decode a (H, W, 5) float32 ugriz .npy cutout in the browser and composite it into
// an RGB texture so a galaxy renders as its actual image (not just a coloured dot).
// Bands -> colour: i->R, r->G, g->B (a gri composite), per-band asinh stretch scaled
// to a high percentile so the faint disk shows without blowing out the core.
import * as THREE from 'three'

// Parse a NumPy .npy buffer -> { h, w, c, data:Float32Array }. Assumes '<f4' little-endian
// (what the cutouts are). The header is padded so the data offset is 64-byte aligned.
function parseNpy(buf) {
  const dv = new DataView(buf)
  const magic = String.fromCharCode(...new Uint8Array(buf, 1, 5))
  if (magic !== 'NUMPY') throw new Error('not a .npy file')
  const headerLen = dv.getUint16(8, true)
  const header = new TextDecoder().decode(new Uint8Array(buf, 10, headerLen))
  if (!/'descr':\s*'[<|]f4'/.test(header)) throw new Error('expected float32 .npy')
  const shape = header.match(/'shape':\s*\(([^)]*)\)/)[1]
    .split(',').map((s) => parseInt(s, 10)).filter((n) => !Number.isNaN(n))
  const [h, w, c] = shape
  const data = new Float32Array(buf, 10 + headerLen, h * w * c)
  return { h, w, c, data }
}

// Two percentiles of one band from a single strided copy + sort. Returns [lo, hi]:
// lo ≈ the sky level (black point), hi ≈ the bright reference for scaling.
function bandLoHi(data, c, band, n, pLo, pHi) {
  const v = new Float32Array(n)
  for (let i = 0; i < n; i++) v[i] = data[i * c + band]
  v.sort()
  const at = (p) => v[Math.min(n - 1, Math.max(0, Math.floor(p * (n - 1))))] || 0
  return [at(pLo), at(pHi)]
}

// Color-preserving arcsinh (Lupton) ugriz -> RGB, matching the diff4_lupton viewer:
// per-band normalize by the 99th pct, mix R=.20r+.40i+.40z, G=.35g+.65r, B=.58u+.42g,
// then asinh(Q·I)/asinh(Q) applied as a per-pixel scale so hue is preserved. Q=8 (viewer default).
const Q = 8
// Noise control: SKY_PCT is the per-band black point (subtract this percentile as sky, clip
// negatives to black) and FLOOR is an intensity black point with a soft knee that crushes the
// residual sky speckle the asinh stretch would otherwise lift. Raise either to clean more sky.
const SKY_PCT = 0.55
const FLOOR = 0.05

// ArrayBuffer of a (H,W,5) ugriz cutout -> an HTMLCanvasElement with the Lupton gri composite
// (black sky). Shared by the 3D texture and the Grad-CAM overlay.
// crop (optional): center-crop to crop×crop first — used by Grad-CAM so the base image matches
// exactly what the backend feeds the model (center-crop to CROP), keeping the heatmap aligned.
export function npyToCanvas(buf, crop = null) {
  let { h, w, c, data } = parseNpy(buf)
  if (crop && (h > crop || w > crop)) {            // center-crop to crop×crop (what the model sees)
    const sh = (h - crop) >> 1, sw = (w - crop) >> 1
    const out = new Float32Array(crop * crop * c)
    for (let y = 0; y < crop; y++)
      for (let x = 0; x < crop; x++)
        for (let b = 0; b < c; b++)
          out[(y * crop + x) * c + b] = data[((sh + y) * w + (sw + x)) * c + b]
    data = out; h = w = crop
  }
  const n = h * w
  // per-band sky (black point) + scale: map [SKY_PCT pct .. 99th pct] -> [0 .. 1] for u,g,r,i,z
  const sky = [], inv = []
  for (let b = 0; b < 5; b++) {
    const [lo, hi] = bandLoHi(data, c, Math.min(b, c - 1), n, SKY_PCT, 0.99)
    sky[b] = lo; inv[b] = 1 / Math.max(hi - lo, 1e-6)
  }
  const aq = Math.asinh(Q)

  const canvas = document.createElement('canvas')
  canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  const img = ctx.createImageData(w, h)
  for (let p = 0; p < n; p++) {
    const o = p * c
    // subtract per-band sky, clip negative noise to black
    const u = Math.max(0, (data[o] - sky[0]) * inv[0]), g = Math.max(0, (data[o + 1] - sky[1]) * inv[1])
    const r = Math.max(0, (data[o + 2] - sky[2]) * inv[2]), i = Math.max(0, (data[o + 3] - sky[3]) * inv[3])
    const z = Math.max(0, (data[o + 4] - sky[4]) * inv[4])
    const R = 0.20 * r + 0.40 * i + 0.40 * z
    const G = 0.35 * g + 0.65 * r
    const B = 0.58 * u + 0.42 * g
    const I = (R + G + B) / 3
    // intensity black point with a soft knee: sky residual below FLOOR -> 0, hue preserved (÷I)
    const s = I > 1e-6 ? (Math.asinh(Q * Math.max(0, I - FLOOR)) / aq) / I : 0
    img.data[p * 4 + 0] = 255 * Math.max(0, Math.min(1, R * s))
    img.data[p * 4 + 1] = 255 * Math.max(0, Math.min(1, G * s))
    img.data[p * 4 + 2] = 255 * Math.max(0, Math.min(1, B * s))
    img.data[p * 4 + 3] = 255
  }
  ctx.putImageData(img, 0, 0)
  return canvas
}

// ---- 3D-scene render path (SEPARATE from npyToCanvas / Grad-CAM; do not unify) ----
// Same Lupton composite, but tuned for the floating billboards: a more aggressive sky black
// point, and a luminance ALPHA so darker pixels are more transparent (the noisy sky fades to
// nothing while the galaxy stays solid). Grad-CAM keeps npyToCanvas (opaque) untouched.
const SKY_SCENE = 0.65    // per-band sky black point (higher = cleaner sky, eats faint outskirts)
const FLOOR_SCENE = 0.09  // intensity black point (soft knee)
const ALPHA_GAMMA = 1.4   // >1 pushes dim pixels harder toward transparent

function npyToSceneCanvas(buf) {
  const { h, w, c, data } = parseNpy(buf)
  const n = h * w
  const sky = [], inv = []
  for (let b = 0; b < 5; b++) {
    const [lo, hi] = bandLoHi(data, c, Math.min(b, c - 1), n, SKY_SCENE, 0.99)
    sky[b] = lo; inv[b] = 1 / Math.max(hi - lo, 1e-6)
  }
  const aq = Math.asinh(Q)
  const canvas = document.createElement('canvas')
  canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  const img = ctx.createImageData(w, h)
  for (let p = 0; p < n; p++) {
    const o = p * c
    const u = Math.max(0, (data[o] - sky[0]) * inv[0]), g = Math.max(0, (data[o + 1] - sky[1]) * inv[1])
    const r = Math.max(0, (data[o + 2] - sky[2]) * inv[2]), i = Math.max(0, (data[o + 3] - sky[3]) * inv[3])
    const z = Math.max(0, (data[o + 4] - sky[4]) * inv[4])
    const R = 0.20 * r + 0.40 * i + 0.40 * z
    const G = 0.35 * g + 0.65 * r
    const B = 0.58 * u + 0.42 * g
    const I = (R + G + B) / 3
    const s = I > 1e-6 ? (Math.asinh(Q * Math.max(0, I - FLOOR_SCENE)) / aq) / I : 0
    const Ro = Math.max(0, Math.min(1, R * s)), Go = Math.max(0, Math.min(1, G * s)), Bo = Math.max(0, Math.min(1, B * s))
    img.data[p * 4 + 0] = 255 * Ro
    img.data[p * 4 + 1] = 255 * Go
    img.data[p * 4 + 2] = 255 * Bo
    img.data[p * 4 + 3] = 255 * Math.pow(Math.max(Ro, Go, Bo), ALPHA_GAMMA)  // darker -> more transparent
  }
  ctx.putImageData(img, 0, 0)
  return canvas
}

// ArrayBuffer of a (H,W,5) ugriz cutout -> THREE.CanvasTexture (sRGB) for the 3D scene.
// Built from npyToSceneCanvas (sky-transparent), then supersampled: the raw cutout is only
// 64×64, so a near billboard would show a hard pixel grid. We supersample into a larger canvas
// with high-quality smoothing plus a hair of blur (≈0.4 source px) to dissolve the grid, then
// let mipmaps + anisotropy keep it clean when the galaxy is small/far.
const SS = 4                                    // supersample factor (64 -> 256, power-of-two)

export function npyToTexture(buf) {
  const src = npyToSceneCanvas(buf)
  const big = document.createElement('canvas')
  big.width = src.width * SS
  big.height = src.height * SS
  const ctx = big.getContext('2d')
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.filter = `blur(${SS * 0.4}px)`            // at SS× scale this is ~0.4 px of the source
  ctx.drawImage(src, 0, 0, big.width, big.height)

  const tex = new THREE.CanvasTexture(big)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.magFilter = THREE.LinearFilter
  tex.minFilter = THREE.LinearMipmapLinearFilter // trilinear mipmaps -> no shimmer when minified
  tex.generateMipmaps = true
  tex.anisotropy = 8                             // crisp at grazing angles; three clamps to GPU max
  return tex
}
