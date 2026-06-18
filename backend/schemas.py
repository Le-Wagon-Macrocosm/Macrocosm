"""Pydantic request/response models.  TASK 04."""
from typing import Optional
from pydantic import BaseModel

# TODO (task 04): define two models, then delete this comment.
#   TabularInput     - one Optional[float] = None per raw catalog field (settings.RAW_TABULAR_FIELDS)
#   PredictResponse  - z: float ; distance_gly, z_lo, z_hi : Optional[float] = None

class TabularInput:
    def __init__(self,
                 dered_u: Optional[float] = None,
                 dered_g: Optional[float] = None,
                 dered_r: Optional[float] = None,
                 dered_i: Optional[float] = None,
                 dered_z: Optional[float] = None,
                 expRad_r: Optional[float] = None,
                 deVRad_r: Optional[float] = None,
                 petroRad_r: Optional[float] = None,
                 petroR50_r: Optional[float] = None,
                 petroR90_r: Optional[float] = None,
                 fracDeV_r: Optional[float] = None):
        self.dered_u = dered_u
        self.dered_g = dered_g
        self.dered_r = dered_r
        self.dered_i = dered_i
        self.dered_z = dered_z
        self.expRad_r = expRad_r
        self.deVRad_r = deVRad_r
        self.petroRad_r = petroRad_r
        self.petroR50_r = petroR50_r
        self.petroR90_r = petroR90_r
        self.fracDeV_r = fracDeV_r

class PredictResponse(BaseModel):
    z: float
    distance_gly: float | None = None
    z_lo: float | None = None
    z_hi: float | None = None
