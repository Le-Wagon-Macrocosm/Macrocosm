"""Backend settings (env-overridable).  TASK 01 -> implement Settings."""
import os


class Settings:
    #   BASELINE_PATH      env "BASELINE_PATH",   default the baseline pkl path under models/
    #   IMAGE_MODEL_PATH   env "IMAGE_MODEL_PATH", default the keras image model path under models/
    #   IMG_SHAPE          the (h, w, bands) of one ugriz cutout
    #   CROP               model input crop S (env "CROP"), an int <= image height
    #   TABULAR_FEATURES   the 16 feature names the baseline expects, IN ORDER (see the task notebook)
    #   RAW_TABULAR_FIELDS the raw catalog columns a request carries (engineered -> the 16)
    #   CORS_ORIGINS       allowed origins, env "CORS_ORIGINS" comma-separated
    #   TITLE              the API title
    def __init__(self):
        self.BASELINE_PATH = os.environ.get("BASELINE_PATH", "../models/baseline_stack.pkl")
        self.IMAGE_MODEL_PATH = os.environ.get("IMAGE_MODEL_PATH", "../models/dcmdn.keras")
        self.IMG_SHAPE = (24, 24, 5)
        self.CROP = int(os.environ.get("CROP", 24))
        self.TABULAR_FEATURES = ["dered_u","dered_g","dered_r","dered_i","dered_z","g-r","u-g","r-i","i-z","log_expRad_r","log_deVRad_r","log_petroRad_r","log_petroR50_r","log_petroR90_r","fracDeV_r","conc_r"]
        self.RAW_TABULAR_FIELDS = ["dered_u","dered_g","dered_r","dered_i","dered_z","expRad_r","deVRad_r","petroRad_r","petroR50_r","petroR90_r","fracDeV_r"]
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        self.TITLE = "Macrocosm photo-z API"


settings = Settings()
