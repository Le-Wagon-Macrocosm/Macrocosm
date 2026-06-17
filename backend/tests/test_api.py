"""API contract tests.  TASK 11.

Build TINY fixtures (a small fake baseline dict {'model','features'} + the fake image model),
point BASELINE_PATH / IMAGE_MODEL_PATH at them *before* importing backend.main, then test:
  - GET /                              -> 200, status "ok"
  - POST /predict image-only          -> 200, has z + distance_gly
  - POST /predict image + tabular JSON -> 200
  - POST /predict a 32x32x5 cutout     -> 422
"""
# TODO (task 11)
