"""Pydantic request/response models.  TASK 04."""
from typing import Optional

from pydantic import BaseModel


class TabularInput(BaseModel):
    """Optional raw catalog fields (settings.RAW_TABULAR_FIELDS); any may be missing."""
    dered_u: Optional[float] = None
    dered_g: Optional[float] = None
    dered_r: Optional[float] = None
    dered_i: Optional[float] = None
    dered_z: Optional[float] = None
    expRad_r: Optional[float] = None
    deVRad_r: Optional[float] = None
    petroRad_r: Optional[float] = None
    petroR50_r: Optional[float] = None
    petroR90_r: Optional[float] = None
    fracDeV_r: Optional[float] = None


class PredictResponse(BaseModel):
    z: float
    distance_gly: Optional[float] = None
    z_lo: Optional[float] = None
    z_hi: Optional[float] = None


class ExplainResponse(BaseModel):
    """Grad-CAM saliency for one cutout: the redshift point estimate + a CROP x CROP heatmap in [0,1]."""
    redshift: float
    heatmap: list[list[float]]
