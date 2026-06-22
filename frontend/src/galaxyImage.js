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

const Q = 8 // asinh softening: higher -> more faint-feature boost
const stretch = (x, scale) =>
  Math.min(1, Math.asinh((Q * Math.max(0, x)) / scale) / Math.asinh(Q))

// ArrayBuffer of a ugriz cutout -> THREE.CanvasTexture (sRGB). The sky is made
// TRANSPARENT (alpha from brightness) so the galaxy isn't a square tile.
export function npyToTexture(buf) {
  const { h, w, c, data } = parseNpy(buf)
  const n = h * w
  // R=i(3) G=r(2) B=g(1); fall back to single band if there are fewer channels
  const bands = [Math.min(3, c - 1), Math.min(2, c - 1), Math.min(1, c - 1)]
  // per band: subtract a sky floor (median) so the background -> ~0, then scale by
  // the 99.5th percentile ABOVE that floor.
  const sky = bands.map((b) => bandPercentile(data, c, b, n, 0.5))
  const scales = bands.map((b, k) => Math.max(1e-6, bandPercentile(data, c, b, n, 0.995) - sky[k]))

  const canvas = document.createElement('canvas')
  canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  const img = ctx.createImageData(w, h)
  for (let p = 0; p < n; p++) {
    const o = p * c
    const r = stretch(data[o + bands[0]] - sky[0], scales[0])
    const g = stretch(data[o + bands[1]] - sky[1], scales[1])
    const b = stretch(data[o + bands[2]] - sky[2], scales[2])
    img.data[p * 4 + 0] = 255 * r
    img.data[p * 4 + 1] = 255 * g
    img.data[p * 4 + 2] = 255 * b
    // alpha from brightness: sky (~0) fades out, galaxy stays solid -> no square edge
    img.data[p * 4 + 3] = 255 * Math.min(1, 1.2 * Math.max(r, g, b))
  }
  ctx.putImageData(img, 0, 0)

  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.magFilter = THREE.LinearFilter
  tex.minFilter = THREE.LinearFilter
  return tex
}

// A soft radial glow (white core -> transparent) reused, tinted by the material colour,
// as the galaxy's z-colour halo — so the colour cue is a glow, not a square.
let _halo
export function haloTexture() {
  if (_halo) return _halo
  const s = 64
  const cv = document.createElement('canvas'); cv.width = cv.height = s
  const ctx = cv.getContext('2d')
  const grad = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2)
  grad.addColorStop(0, 'rgba(255,255,255,0.85)')
  grad.addColorStop(0.45, 'rgba(255,255,255,0.2)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = grad; ctx.fillRect(0, 0, s, s)
  _halo = new THREE.CanvasTexture(cv)
  _halo.colorSpace = THREE.SRGBColorSpace
  return _halo
}
