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
    stack, cnn, fusion = get_models()
    return {
        "status": "ok",
        "tabular_stack": type(stack).__name__,
        "image_cnn":     getattr(cnn, "name", type(cnn).__name__),
        "fusion_model":  getattr(fusion, "name", type(fusion).__name__),
        "input_shape":   settings.IMG_SHAPE,
    }


def parse_tabular(tabular: str | None):
    """tabular JSON string (or None) -> (X16 with NaN, mask) or None. 422 on bad JSON/fields."""
    if tabular is None:
        return None
    try:
        row = TabularInput(**json.loads(tabular)).model_dump()
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON for tabular data")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid tabular fields: {e}")
    return tabular_features(row)          # (X16, mask)


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

    # Parse tabular data if provided -> (X16, mask); None -> fusion leans on the image
    tabular_data = parse_tabular(tabular)

    # Run the fused prediction (CNN embedding + tabular bases -> fusion MDN -> z)
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
def explain_route(
    file: UploadFile = File(...),
    tabular: str | None = Form(None),   # optional; sharpens the redshift, heatmap is image-only
):
    # Get File Image (1, CROP, CROP, 5)
    image = get_image(file)

    # Optional tabular -> (X16, mask); absent -> median-imputed bases + zero mask
    parsed = parse_tabular(tabular)
    X16, mask = parsed if parsed is not None else (None, None)

    result = explain(image, X16=X16, mask=mask)   # Grad-CAM: redshift + (CROP x CROP) heatmap

    return ExplainResponse(
        redshift=float(result["redshift"]),
        heatmap=result["heatmap"].tolist(),
    )
