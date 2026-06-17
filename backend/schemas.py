"""Pydantic request / response models.  TASK 02."""
from typing import List
from pydantic import BaseModel, Field

# TODO: PredictRequest  -> images: batch of 64x64x5 cutouts, shape (n, 64, 64, 5)
# TODO: Prediction      -> z_pred: float
# TODO: PredictResponse -> model: str, n: int, predictions: List[Prediction]
