"""Macrocosm backend — FastAPI inference service.

Minimal scaffold: the full API surface is defined, but the real handlers are
stubs that return **501 Not Implemented** until the model lands. `/health` is
kept live so `make backend` can confirm the server boots.

Run locally: `make backend`  (http://localhost:8000, docs at /docs)
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

# --- model lifecycle -------------------------------------------------------
# The model is loaded ONCE at startup from $MODEL_URI (e.g. gs://… on Cloud Run)
# and kept in memory for every request. Placeholder for now.
MODEL = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL
    # TODO: load model from os.environ["MODEL_URI"] into MODEL (download from GCS -> RAM)
    yield
    # TODO: cleanup if needed


app = FastAPI(title="Macrocosm", version="0.0.1", lifespan=lifespan)

# TODO: enable CORS for the GitHub Pages frontend origin (front/back are separate):
#   from fastapi.middleware.cors import CORSMiddleware
#   app.add_middleware(CORSMiddleware, allow_origins=["https://<org>.github.io"],
#                      allow_methods=["*"], allow_headers=["*"])


# --- schemas ---------------------------------------------------------------
class PredictionResponse(BaseModel):
    z: float
    distance_gly: float
    z_lo: Optional[float] = None      # uncertainty placeholders — filled in later
    z_hi: Optional[float] = None


class ModelInfo(BaseModel):
    name: str
    version: str
    loaded: bool


# --- endpoints -------------------------------------------------------------
@app.get("/")
def root():
    """Service info."""
    return {"service": "macrocosm", "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness check (used by Cloud Run / monitoring)."""
    return {"status": "ok"}


@app.get("/model/info", response_model=ModelInfo)
def model_info():
    """Which model is currently loaded (supports the baseline→CNN swap)."""
    raise HTTPException(status_code=501, detail="not implemented")


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    image: UploadFile = File(..., description=".npy or FITS cutout — (64,64,5) float array"),
    tabular: Optional[str] = Form(None, description="photometry as a JSON string"),
    ra: Optional[float] = Form(None, description="RA in degrees (for placing in 3D)"),
    dec: Optional[float] = Form(None, description="Dec in degrees"),
):
    """Predict redshift z (+ distance) from a single galaxy cutout."""
    raise HTTPException(status_code=501, detail="not implemented")
