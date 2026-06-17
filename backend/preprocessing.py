"""Raw payload -> model-ready array.  TASK 03."""
import numpy as np
from .config import settings


def prepare_images(images) -> np.ndarray:
    """Validate + stack cutouts into a float32 (n, 64, 64, 5) array. Accept a single
    (64,64,5) image or a batch. Raise ValueError on wrong shape / empty batch."""
    # TODO
    raise NotImplementedError
