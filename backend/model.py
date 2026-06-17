"""Load the model artifact and run predictions.  TASK 04 (load) + TASK 07 (predict)."""
import joblib
from .config import settings

_model = None


def load_model(path: str = None):
    """Load the pickle into the module cache and return it."""
    # TODO  (TASK 04)
    raise NotImplementedError


def get_model():
    """Return the cached model, loading it on first use."""
    # TODO  (TASK 04)
    raise NotImplementedError


def predict_z(images_array):
    """(n,64,64,5) -> list[float] predicted redshifts."""
    # TODO  (TASK 07)
    raise NotImplementedError
