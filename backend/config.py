"""Backend settings (env-overridable).  TASK 01 -> implement Settings."""
import os


class Settings:
    # TODO (task 01): define the settings the rest of the backend imports. You need:
    #   BASELINE_PATH      env "BASELINE_PATH",   default the baseline pkl path under models/
    #   IMAGE_MODEL_PATH   env "IMAGE_MODEL_PATH", default the fake image pkl path under models/
    #   IMG_SHAPE          the (h, w, bands) of one ugriz cutout
    #   CROP               model input crop S (env "CROP"), an int <= image height
    #   TABULAR_FEATURES   the 16 feature names the baseline expects, IN ORDER (see the task notebook)
    #   RAW_TABULAR_FIELDS the raw catalog columns a request carries (engineered -> the 16)
    #   CORS_ORIGINS       allowed origins, env "CORS_ORIGINS" comma-separated
    #   TITLE              the API title
    pass


settings = Settings()
