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

    clean = {}

    for name in settings.RAW_TABULAR_FIELDS:
         value = float(row.get(name, np.nan))
         clean[name] = np.nan if value <= SENTINEL else value

    features = [
        clean['dered_u'],
        clean['dered_g'],
        clean['dered_r'],
        clean['dered_i'],
        clean['dered_z'],

        np.clip(clean['dered_g'] - clean['dered_r'], -1, 4),
        np.clip(clean['dered_u'] - clean['dered_g'], -1, 4),
        np.clip(clean['dered_r'] - clean['dered_i'], -1, 4),
        np.clip(clean['dered_i'] - clean['dered_z'], -1, 4),

        np.log1p(max(clean['expRad_r'], 0)),
        np.log1p(max(clean['deVRad_r'], 0)),
        np.log1p(max(clean['petroRad_r'], 0)),
        np.log1p(max(clean['petroR50_r'], 0)),
        np.log1p(max(clean['petroR90_r'], 0)),

        clean['fracDeV_r'],

        (
            clean['petroR90_r'] / clean['petroR50_r']
            if np.isfinite(clean['petroR90_r'])
            and np.isfinite(clean['petroR50_r'])
            and clean['petroR50_r'] != 0
            else np.nan
        )
    ]

    X = np.asarray(features, dtype=np.float32)
    mask = np.isfinite(X).astype(np.float32)

    X[~np.isfinite(X)] = 0.0

    return X, mask


def preprocess_image(arr, crop=24, IMG_SHAPE=(24,24,5)):
    """arr: (64,64,5) or (n,64,64,5) -> (n,S,S,5) float32.
    Center-crop to settings.CROP, arcsinh stretch, per-image per-channel normalize.
    Raise ValueError on a wrong-shaped cutout."""

    # Validate Shape
    if not isinstance(arr, np.ndarray):
        raise TypeError(f"Expected numpy array, got {type(arr).__name__}")

    if arr.ndim == 3:
        arr = arr[np.newaxis, ...]

    if arr.shape[1:] != IMG_SHAPE:
        raise ValueError(f"Expected IMG_SHAPE, got {arr.shape[1:]}")

    # Center Crop
    N, h, w, C = arr.shape
    if (h < crop or w < crop) and crop != None:
        raise ValueError(
            f"Image dimensions ({h}x{w}) are smaller than crop size ({crop}x{crop})"
        )

    start_h = (h - crop) // 2
    start_w = (w - crop) // 2

    cropped_img = arr[:, start_h:start_h+crop, start_w:start_w+crop, :]

    # Arcsinh Transformation to supress bright images, compressing outliers & preserve sine
    transformed = np.arcsinh(cropped_img)

    # Normalization
    # Compute mean and std across batch (0), height (1), and width (2) for each channel (3)
    mean = transformed.mean(axis=(1, 2), keepdims=True)
    std = transformed.std(axis=(1, 2), keepdims=True)
    # Prevent normalization err if std is 0
    std[std==0] = 1.0

    normalized = (transformed - mean) / std

    return normalized
