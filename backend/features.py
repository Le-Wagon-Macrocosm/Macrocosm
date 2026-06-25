"""Shared preprocessing — identical in training and serving.

Image:   center-crop to CROP, then per-band p99 normalize (x / BAND_P99). Mirrors the CNN's
         preproc='p99' (NO arcsinh, NO per-image standardize).
Tabular: the 16 engineered features (NaN where unmeasured) + a presence mask. NaNs are KEPT here
         (the tabular bases get median-imputed downstream); the mask carries the missingness signal.
"""
import numpy as np
from .config import settings

SENTINEL = -100.0  # SDSS -9999 'not measured' -> NaN at/below this


def tabular_features(row):
    """row: dict of settings.RAW_TABULAR_FIELDS -> (X[16] float32 with NaN where absent, mask[16] float32).

    Mirrors the v4 fusion recipe (fusion.tabular_features): sentinel<=-100 -> NaN; colours = dered
    diffs clip(-1,4); log1p radii (negative -> NaN); conc_r = petroR90_r/petroR50_r. mask[i]=1 if
    feature i is present (finite) else 0 — matching the mask the fusion model was trained on."""
    def g(name):
        v = row.get(name)
        v = float(v) if v is not None else np.nan
        return np.nan if v <= SENTINEL else v

    du, dg, dr, di, dz = (g(f"dered_{b}") for b in "ugriz")

    def logr(name):
        v = g(name)
        return np.log1p(v) if (np.isfinite(v) and v >= 0) else np.nan

    R50, R90 = g("petroR50_r"), g("petroR90_r")

    feats = [
        du, dg, dr, di, dz,
        np.clip(dg - dr, -1, 4), np.clip(du - dg, -1, 4),
        np.clip(dr - di, -1, 4), np.clip(di - dz, -1, 4),
        logr("expRad_r"), logr("deVRad_r"), logr("petroRad_r"),
        np.log1p(R50) if (np.isfinite(R50) and R50 >= 0) else np.nan,
        np.log1p(R90) if (np.isfinite(R90) and R90 >= 0) else np.nan,
        g("fracDeV_r"),
        (R90 / R50) if (np.isfinite(R90) and np.isfinite(R50) and R50 != 0) else np.nan,
    ]
    X = np.asarray(feats, dtype=np.float32)
    X[~np.isfinite(X)] = np.nan                  # keep NaN (do NOT zero-fill): bases get median-imputed
    mask = np.isfinite(X).astype(np.float32)     # presence: 1=measured (matches fusion training mask)
    return X, mask


def preprocess_image(arr, crop=None, band_p99=None):
    """arr: (S,S,5) or (n,S,S,5) ugriz nanomaggies, S>=CROP -> (n,CROP,CROP,5) float32.

    Center-crop to CROP, then per-band p99 normalize (x / BAND_P99) — exactly the CNN's preproc='p99'.
    The v4 model was trained on center-crop-24 stamps, so we crop (NOT resize) at inference too.
    Raise ValueError on a wrong-shaped / too-small cutout."""
    crop = settings.CROP if crop is None else crop
    p99 = np.asarray(settings.BAND_P99 if band_p99 is None else band_p99, dtype=np.float32)
    bands = settings.IMG_SHAPE[-1]

    if not isinstance(arr, np.ndarray):
        raise TypeError(f"Expected numpy array, got {type(arr).__name__}")
    if arr.ndim == 3:
        arr = arr[np.newaxis, ...]
    if arr.ndim != 4 or arr.shape[-1] != bands:
        raise ValueError(f"Expected a (...,{bands}) ugriz cutout, got {arr.shape}")

    n, h, w, c = arr.shape
    if h < crop or w < crop:
        raise ValueError(f"Image {h}x{w} is smaller than crop {crop}x{crop}")
    sh, sw = (h - crop) // 2, (w - crop) // 2
    cropped = arr[:, sh:sh + crop, sw:sw + crop, :].astype(np.float32)
    return cropped / p99                          # (n, crop, crop, 5)
