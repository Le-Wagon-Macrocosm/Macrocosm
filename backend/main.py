"""FastAPI app for image-based photo-z prediction.  TASK 05 (GET /) + TASK 08 (POST /predict)."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from .config import settings
# TODO import schemas / preprocessing / model as you need them


# TODO (TASK 05): load the model on startup via a lifespan handler, then create `app`
# @asynccontextmanager
# async def lifespan(app): ...; yield
# app = FastAPI(title=settings.TITLE, lifespan=lifespan)


# TODO (TASK 05): GET /  -> {"status": "ok", "model": <class name>, "input_shape": settings.IMG_SHAPE}


# TODO (TASK 08): POST /predict  (req -> prepare_images -> predict_z -> PredictResponse; 422 on ValueError)
