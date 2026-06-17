"""FastAPI app — single fused /predict (image + optional tabular -> z, distance).
TASK 07 -> app + lifespan + CORS + GET "/" ; TASK 10 -> POST "/predict"."""
import io
import json
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import TabularInput, PredictResponse
from .features import preprocess_image, tabular_features
from .model import load_models, get_models, predict_z
from .cosmology import z_to_distance_gly

# TODO (task 07): build the app:
#   - an async lifespan handler that calls load_models() then `yield`
#   - app = FastAPI(title=settings.TITLE, lifespan=lifespan)
#   - app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
#   - @app.get("/") health route -> {"status":"ok", model names, "input_shape": settings.IMG_SHAPE}

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield


app = FastAPI(title=settings.TITLE, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    baseline, image = get_models()
    return {
        "status": "ok",
        "tabular_model": type(baseline).__name__,
        "image_model":   type(image).__name__,
        "input_shape":   settings.IMG_SHAPE,
    }

# TODO (task 10): add @app.post("/predict", response_model=PredictResponse):
#   read the .npy cutout from the upload -> preprocess_image (ValueError -> HTTP 422);
#   if a tabular JSON part is present -> TabularInput -> tabular_features -> (n,16);
#   predict_z(imgs, feats) -> z; return PredictResponse(z=z, distance_gly=z_to_distance_gly(z)).

# raise NotImplementedError("implement the app — task 07 (health) then task 10 (predict)")
