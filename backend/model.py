"""Load artifacts + run the (placeholder) fused prediction.
TASK 06 -> load_models / get_models ; TASK 09 -> predict_z.

Serving interface = the FINAL fused model's (image + optional tabular -> z). Placeholder today:
real tabular baseline for the tabular branch, fake image model for the image branch."""
import os
import joblib
import numpy as np
from .config import settings
from .dcmdn_model import mdn_loss


def _baseline_path():
    return getattr(settings, "BASELINE_PATH",
                   os.environ.get("BASELINE_PATH", "models/baseline_stack.pkl"))

def _image_path():
    return getattr(settings, "IMAGE_MODEL_PATH",
                   os.environ.get("IMAGE_MODEL_PATH", "models/dcmdn.keras"))

_baseline = None   # sklearn StackingRegressor (16 features)
_image = None       # fake image model (.predict((n,S,S,5)) -> (n,))


def load_models():
    """Load both artifacts into the module cache and return (baseline, image).
    The baseline pickle is a dict {'model','features',...}; the image artifact is a bare model."""
    global _baseline, _image
    _baseline = joblib.load(_baseline_path())["model"]            # tabular baseline: always a pickle
    p = _image_path()
    if p.endswith((".keras", ".h5")):                            # CNN image model: keras/h5
        import tensorflow as tf
        _image = tf.keras.models.load_model(
            p, compile=False
        )

    else:                                                        # fallback (e.g. the fake .pkl image model / tests)
        _image = joblib.load(p)
    return _baseline, _image


def get_models():
    """Return (baseline, image), loading them on first call."""
    global _baseline, _image
    if _baseline is None or _image is None:
        load_models()
    return _baseline, _image



def predict_z(images, tabular=None):
    """images: (n,S,S,5) preprocessed. tabular: (n,16) feature matrix or None. -> list[float].
    Placeholder fusion: tabular present -> baseline.predict; else -> image.predict."""
    baseline, image = get_models()
    if tabular is not None:
        return baseline.predict(tabular.reshape(-1,16)).tolist()
    else:
        return image.predict(images).tolist()
