"""Load the v4 fusion photo-z stack and run image(+optional tabular) -> z.

Composite serving model:
  image  --CNN(photoz_cnn)--> 'embedding' (64-d)
  tabular --baseline_stack_v4 (3 frozen bases)--> 3 base preds + 16 presence mask
  [3 base | 16 mask | 64 emb] (83-d) --fusion MLP+MDN--> z   (MDN K=5: pi,mu,sigma)

Absent tabular -> median-imputed bases + an all-zero presence mask (the fusion leans on the image).
"""
import joblib
import numpy as np
from .config import settings

_stack = None       # v4 FrozenStack dict {'bases': {RF,HGB,MLP}, 'base_order': [...]}
_cnn = None         # keras photoz_cnn (image -> z); we tap its 'embedding'
_embedder = None    # keras Model: cnn.input -> 'embedding' (64-d)
_fusion = None      # keras fusion MLP+MDN: (n,83) -> (n,15)
_medians = None     # (16,) train medians, to impute absent tabular features


def load_models():
    """Load CNN + fusion + tabular stack + medians into the module cache. Returns (stack, cnn, fusion)."""
    global _stack, _cnn, _embedder, _fusion, _medians
    import tensorflow as tf

    _stack = joblib.load(settings.BASELINE_PATH)
    if isinstance(_stack, dict) and "bases" not in _stack and "model" in _stack:
        _stack = _stack["model"]                       # tolerate a {'model': FrozenStack} wrapper

    _cnn = tf.keras.models.load_model(settings.CNN_MODEL_PATH, compile=False)
    _embedder = tf.keras.Model(_cnn.input, _cnn.get_layer("embedding").output, name="cnn_embedder")
    _fusion = tf.keras.models.load_model(settings.FUSION_MODEL_PATH, compile=False)
    _medians = np.load(settings.MEDIANS_PATH).astype("float32")
    return _stack, _cnn, _fusion


def get_models():
    """Return (stack, cnn, fusion), loading on first call."""
    if _fusion is None:
        load_models()
    return _stack, _cnn, _fusion


def embedder():
    """Keras Model mapping a preprocessed cutout -> its 64-d CNN 'embedding'."""
    if _embedder is None:
        load_models()
    return _embedder


def tabular_base_preds(X16, mask):
    """X16/mask: (16,) or (n,16). NaN in X16 -> median-imputed, then 3 base preds (RF/HGB/MLP).
    Returns (base (n,3) float32, mask (n,16) float32) ready for the fusion vector."""
    get_models()
    X = np.atleast_2d(np.asarray(X16, "float32"))
    m = np.atleast_2d(np.asarray(mask, "float32"))
    Xi = np.where(np.isnan(X), _medians, X).astype("float32")   # bases were fit on dropna'd data
    if isinstance(_stack, dict) and "bases" in _stack:
        base = np.column_stack([_stack["bases"][b].predict(Xi) for b in _stack["base_order"]])
    else:                                                       # sklearn StackingRegressor fallback
        base = _stack.transform(Xi)
    return base.astype("float32"), m


def fusion_vector(images, X16=None, mask=None):
    """images: (n,CROP,CROP,5) preprocessed (p99). -> (n,83) [3 base | 16 mask | 64 emb] for the fusion.
    X16/mask None -> absent tabular (all-NaN -> median-imputed bases, zero mask)."""
    emb = embedder().predict(images, verbose=0)                 # (n,64)
    n = len(emb)
    if X16 is None:
        X16 = np.full((1, 16), np.nan, "float32")
        mask = np.zeros((1, 16), "float32")
    base, m = tabular_base_preds(X16, mask)                     # (k,3), (k,16)
    if len(base) == 1 and n > 1:                                # one tabular row, many images
        base = np.repeat(base, n, 0); m = np.repeat(m, n, 0)
    return np.concatenate([base, m, emb], axis=1).astype("float32")


def mdn_point(raw):
    """raw: (n, 3K) [pi,mu,sigma] -> log1p(z) point estimate mu[argmax pi]. Caller applies expm1."""
    raw = np.asarray(raw)
    K = raw.shape[1] // 3
    pi, mu = raw[:, :K], raw[:, K:2 * K]
    return mu[np.arange(len(mu)), pi.argmax(1)]


def predict_z(images, tabular=None):
    """images: (n,CROP,CROP,5) preprocessed. tabular: (X16, mask) | X16 (16,)/(n,16) | None.
    -> list[float] redshift. Fusion over [base | mask | emb]; MDN point estimate; expm1 back to z."""
    _, _, fusion = get_models()
    X16 = mask = None
    if tabular is not None:
        if isinstance(tabular, (tuple, list)) and len(tabular) == 2:
            X16, mask = tabular
        else:
            X16 = np.asarray(tabular, "float32")
            mask = np.isfinite(X16).astype("float32")
    fvec = fusion_vector(images, X16, mask)
    raw = fusion.predict(fvec, verbose=0)                       # (n,15)
    z = np.expm1(mdn_point(raw))
    return [float(v) for v in z]
