// Grad-CAM overlay: the galaxy cutout (Lupton gri composite) with the model's saliency
// heatmap tinted on top (jet colormap, alpha ∝ intensity). The heatmap is the CROP×CROP
// array the /explain endpoint returns; we upscale it smoothly over the galaxy image.
import { npyToCanvas } from './galaxyImage.js'

// scalar t in [0,1] -> [r,g,b] 0..255 on a blue→cyan→green→yellow→red "jet" ramp.
function jet(t) {
  t = Math.max(0, Math.min(1, t))
  const r = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 3)))
  const g = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 2)))
  const b = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * t - 1)))
  return [255 * r, 255 * g, 255 * b]
}

// (npyBuf, heatmap[H][W] in [0,1], display px) -> a square HTMLCanvasElement with the
// galaxy underneath and the jet-tinted saliency on top.
export function gradcamCanvas(npyBuf, heatmap, size = 220) {
  const out = document.createElement('canvas')
  out.width = out.height = size
  const ctx = out.getContext('2d')
  ctx.imageSmoothingEnabled = true

  // 1) galaxy base, upscaled to the display size
  try {
    const base = npyToCanvas(npyBuf, 24)   // center 24×24 the model saw -> heatmap aligns pixel-for-pixel
    ctx.drawImage(base, 0, 0, size, size)
  } catch {
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, size, size)
  }

  // 2) heatmap -> a small RGBA canvas (jet + alpha), then drawn over the galaxy (smoothed upscale)
  const h = heatmap.length, w = heatmap[0].length
  const hm = document.createElement('canvas')
  hm.width = w; hm.height = h
  const himg = hm.getContext('2d').createImageData(w, h)
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const t = heatmap[y][x]
      const [r, g, b] = jet(t)
      const o = (y * w + x) * 4
      himg.data[o] = r; himg.data[o + 1] = g; himg.data[o + 2] = b
      himg.data[o + 3] = 235 * Math.max(0, Math.min(1, t))   // transparent where the model didn't look
    }
  }
  hm.getContext('2d').putImageData(himg, 0, 0)
  ctx.globalAlpha = 0.6
  ctx.drawImage(hm, 0, 0, size, size)
  ctx.globalAlpha = 1
  return out
}

// Render the Grad-CAM result into `mount` (cleared first): the overlay + a caption.
export function showGradcam(mount, npyBuf, result, name = '') {
  mount.innerHTML = ''
  mount.appendChild(gradcamCanvas(npyBuf, result.heatmap))
  const cap = document.createElement('div')
  cap.className = 'gradcam-cap'
  cap.innerHTML = `${name ? `<b>${name}</b> · ` : ''}ẑ=${result.redshift.toFixed(3)}` +
                  ` <span class="muted">· red = where the model reads the redshift</span>`
  mount.appendChild(cap)
}
