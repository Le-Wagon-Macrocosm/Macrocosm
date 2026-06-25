"""Backend settings (env-overridable).

Serving model = the v4 fusion photo-z stack:
  image  --CNN(photoz_cnn, default arch)--> 'embedding' (64-d)
  tabular --baseline_stack_v4 (3 frozen bases)--> 3 base preds  + 16 presence mask
  [3 base | 16 mask | 64 emb] (83-d) --fusion MLP+MDN--> z   (MDN K=5: pi,mu,sigma)
"""
import os


class Settings:
    def __init__(self):
        # tabular baseline: v4 FrozenStack dict {'bases': {RF,HGB,MLP}, 'base_order': [...]} (~664 MB pkl)
        self.BASELINE_PATH = os.environ.get("BASELINE_PATH", "models/baseline_stack_v4.pkl")
        # image CNN (photoz_cnn, default arch); we tap its 'embedding' (64-d) for the fusion
        self.CNN_MODEL_PATH = os.environ.get("CNN_MODEL_PATH", "models/photoz_cnn_v4.h5")
        # fusion MLP+MDN over the 83-d vector -> z (15 = pi,mu,sigma, K=5)
        self.FUSION_MODEL_PATH = os.environ.get("FUSION_MODEL_PATH", "models/fusion_v4.keras")
        # train-set medians (16,) to impute ABSENT tabular features before the bases
        self.MEDIANS_PATH = os.environ.get("MEDIANS_PATH", "models/tabular_medians_v4.npy")

        self.IMG_SHAPE = (24, 24, 5)               # one ugriz cutout fed to the CNN
        self.CROP = int(os.environ.get("CROP", 24))
        # preproc='p99': x / per-band p99 (u,g,r,i,z). crop=24 v4.5 train constants — MUST match the
        # CNN's training preproc, else the embedding (and everything downstream) is wrong.
        self.BAND_P99 = [0.2344, 0.9043, 2.0586, 3.1094, 4.2344]
        self.MDN_K = 5                             # gaussian mixture components

        self.TABULAR_FEATURES = ["dered_u","dered_g","dered_r","dered_i","dered_z","g-r","u-g","r-i","i-z","log_expRad_r","log_deVRad_r","log_petroRad_r","log_petroR50_r","log_petroR90_r","fracDeV_r","conc_r"]
        self.RAW_TABULAR_FIELDS = ["dered_u","dered_g","dered_r","dered_i","dered_z","expRad_r","deVRad_r","petroRad_r","petroR50_r","petroR90_r","fracDeV_r"]
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        self.TITLE = "Macrocosm photo-z API"


settings = Settings()
