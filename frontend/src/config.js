// Backend base URL (the Cloud Run service). Override at build time with
//   VITE_API_BASE=https://… npm run build
// CORS is open on the backend (allow_origins="*"), so the browser can call it directly.
export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  'https://macrocosm-backend-4cqy5oe74a-ew.a.run.app'
