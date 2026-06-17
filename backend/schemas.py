"""Pydantic request/response models.  TASK 04."""
from typing import Optional
from pydantic import BaseModel


# TODO (task 04): define two models, then delete this comment.
#   TabularInput     - one Optional[float] = None per raw catalog field (settings.RAW_TABULAR_FIELDS)
#   PredictResponse  - z: float ; distance_gly, z_lo, z_hi : Optional[float] = None
