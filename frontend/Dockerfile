# Frontend — 3D explorer (Three.js). Node build -> static serve.
# Build context = frontend/  ->  `docker build -t macrocosm-frontend frontend/`
#
# Note: we host the static frontend on GitHub Pages, so this image is OPTIONAL —
# it's here for containerized hosting (HF Spaces / Cloud Run / local). Assumes a
# Node project with a build that outputs ./dist (e.g. Vite).

# ---- build stage ----
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- runtime stage ----
FROM node:22-slim
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist

# Cloud Run injects $PORT (default 8080); HF Spaces expects 7860.
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "serve -s dist -l ${PORT}"]
