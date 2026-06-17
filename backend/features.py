"""Shared preprocessing — identical in training and serving.
TASK 02 -> tabular_features ; TASK 03 -> preprocess_image."""
import numpy as np
from .config import settings

SENTINEL = -100.0  # SDSS -9999 'not measured' -> NaN at/below this


def tabular_features(row):
    """row: dict of settings.RAW_TABULAR_FIELDS -> (X[16] float32, mask[16] float32).
    Clean sentinels (<= -100) to NaN, then engineer the 16 features (recipe in the task
    notebook): 5 dered passthrough, 4 colors = dered diffs clip(-1, 4), 5 log1p sizes,
    fracDeV_r passthrough, conc_r = petroR90_r / petroR50_r. mask[i]=1 if feature i is
    finite else 0 (and that value is filled with 0)."""
    # TODO (task 02)
    raise NotImplementedError


def preprocess_image(arr, crop=None):
    """arr: (64,64,5) or (n,64,64,5) -> (n,S,S,5) float32.
    Center-crop to settings.CROP, arcsinh stretch, per-image per-channel normalize.
    Raise ValueError on a wrong-shaped cutout."""
    # TODO (task 03)
    raise NotImplementedError
