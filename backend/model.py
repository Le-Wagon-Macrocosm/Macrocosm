"""Load artifacts + run the (placeholder) fused prediction.
TASK 06 -> load_models / get_models ; TASK 09 -> predict_z.

Serving interface = the FINAL fused model's (image + optional tabular -> z). Placeholder today:
real tabular baseline for the tabular branch, fake image model for the image branch."""
import joblib
import numpy as np
from .config import settings

_baseline = None   # sklearn StackingRegressor (16 features)
_image = None       # fake image model (.predict((n,S,S,5)) -> (n,))


def load_models():
    """Load both artifacts into the module cache and return (baseline, image).
    The baseline pickle is a dict {'model','features',...}; the image artifact is a bare model."""
    # TODO (task 06)
    raise NotImplementedError


def get_models():
    """Return (baseline, image), loading them on first call."""
    # TODO (task 06)
    raise NotImplementedError


def predict_z(images, tabular=None):
    """images: (n,S,S,5) preprocessed. tabular: (n,16) feature matrix or None. -> list[float].
    Placeholder fusion: tabular present -> baseline.predict; else -> image.predict."""
    # TODO (task 09)
    raise NotImplementedError
