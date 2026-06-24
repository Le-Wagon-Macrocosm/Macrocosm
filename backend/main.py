"""FastAPI app — single fused /predict (image + optional tabular -> z, distance).
TASK 07 -> app + lifespan + CORS + GET "/" ; TASK 10 -> POST "/predict"."""
import io
import json
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import TabularInput, PredictResponse, ExplainResponse
from .features import preprocess_image, tabular_features
from .model import load_models, get_models, predict_z
from .cosmology import z_to_distance_gly

from .gradcam import explain
import time

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
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],  # comma-separated -> list
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

def get_image(file):
    # 1. Load and validate the .npy cutout
    try:
        contents = file.file.read()
        # Reset stream just in case, though read() usually consumes it
        file.file.seek(0)
        cutout = np.load(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid .npy file: {e}")

    # 2. Preprocess the image
    try:
        images = preprocess_image(cutout)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return images


@app.post("/predict", response_model=PredictResponse)
def predict(
    file: UploadFile = File(...),
    ra: float | None = Form(None),    # optional; reserved for placing the prediction in 3D
    dec: float | None = Form(None),
    tabular: str | None = Form(None),
):
    # Get File Image
    image = get_image(file)

    # 3. Parse tabular data if provided: JSON -> TabularInput (validate) -> engineered (16,)
    tabular_data = None
    if tabular is not None:
        try:
            row = TabularInput(**json.loads(tabular)).model_dump()
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid JSON for tabular data")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid tabular fields: {e}")
        X, _mask = tabular_features(row)
        tabular_data = X

    # 4. Run prediction
    # predict_z handles None for either images or tabular_data
    z_list = predict_z(images=image, tabular=tabular_data)

    # Assuming predict_z returns a list, take the first element for single prediction
    if not z_list:
        raise HTTPException(status_code=500, detail="Prediction returned empty result")

    z = float(z_list[0])

    # 5. Calculate distance and return response
    try:
        distance = z_to_distance_gly(z)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating distance: {e}")

    return PredictResponse(z=z, distance_gly=distance)

@app.post("/explain", response_model=ExplainResponse)
def explain_route(file: UploadFile = File(...)):
    # Get File Image
    image = get_image(file)

    result = explain(image)           # one call, gets both ẑ and heatmap

    heatmap = result["heatmap"].tolist()

    return ExplainResponse(redshift=float(result["redshift"]), heatmap=heatmap)
