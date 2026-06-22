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

// High percentile of one band (robust max for scaling), via a strided copy + sort.
function bandPercentile(data, c, band, n, p) {
  const v = new Float32Array(n)
  for (let i = 0; i < n; i++) v[i] = data[i * c + band]
  v.sort()
  return v[Math.min(n - 1, Math.max(0, Math.floor(p * (n - 1))))] || 1e-6
}

// Color-preserving arcsinh (Lupton) ugriz -> RGB, matching the diff4_lupton viewer:
// per-band normalize by the 99th pct, mix R=.20r+.40i+.40z, G=.35g+.65r, B=.58u+.42g,
// then asinh(Q·I)/asinh(Q) applied as a per-pixel scale so hue is preserved. Q=8 (viewer default).
const Q = 8

// ArrayBuffer of a (H,W,5) ugriz cutout -> THREE.CanvasTexture (sRGB). The background
// comes out BLACK (sky normalizes to ~0); the scene draws galaxies with additive
// blending so the black background vanishes and only the galaxy glows — no alpha/halo.
export function npyToTexture(buf) {
  const { h, w, c, data } = parseNpy(buf)
  const n = h * w
  // per-band normalize: 1 / (99th percentile) for each of u, g, r, i, z
  const inv = []
  for (let b = 0; b < 5; b++) inv[b] = 1 / (bandPercentile(data, c, Math.min(b, c - 1), n, 0.99) || 1e-6)
  const aq = Math.asinh(Q)

  const canvas = document.createElement('canvas')
  canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  const img = ctx.createImageData(w, h)
  for (let p = 0; p < n; p++) {
    const o = p * c
    const u = data[o] * inv[0], g = data[o + 1] * inv[1], r = data[o + 2] * inv[2]
    const i = data[o + 3] * inv[3], z = data[o + 4] * inv[4]
    const R = 0.20 * r + 0.40 * i + 0.40 * z
    const G = 0.35 * g + 0.65 * r
    const B = 0.58 * u + 0.42 * g
    const I = (R + G + B) / 3
    const s = I > 1e-6 ? (Math.asinh(Q * Math.max(I, 0)) / aq) / I : 0
    img.data[p * 4 + 0] = 255 * Math.max(0, Math.min(1, R * s))
    img.data[p * 4 + 1] = 255 * Math.max(0, Math.min(1, G * s))
    img.data[p * 4 + 2] = 255 * Math.max(0, Math.min(1, B * s))
    img.data[p * 4 + 3] = 255
  }
  ctx.putImageData(img, 0, 0)

  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.magFilter = THREE.LinearFilter
  tex.minFilter = THREE.LinearFilter
  return tex
}
