import { defineConfig } from 'vite'

// base: './' -> relative asset paths, so the same build works at the domain root
// AND under a GitHub Pages project path (https://<user>.github.io/<repo>/) with no
// hardcoded repo name. The API URL is separate (see src/config.js / VITE_API_BASE).
export default defineConfig({
  base: './',
  build: { outDir: 'dist' },
})
