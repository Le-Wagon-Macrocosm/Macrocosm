"""API contract tests.  TASK 11.

Build TINY fixtures (a small fake baseline dict {'model','features'} + the fake image model),
point BASELINE_PATH / IMAGE_MODEL_PATH at them *before* importing backend.main, then test:
  - GET /                              -> 200, status "ok"
  - POST /predict image-only          -> 200, has z + distance_gly
  - POST /predict image + tabular JSON -> 200
  - POST /predict a 32x32x5 cutout     -> 422
"""
import io, json, tempfile
import joblib
import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from fastapi.testclient import TestClient

# --- tiny fake model fixtures (built once at collection time) ---
_TMP = tempfile.mkdtemp()
joblib.dump({"model": LinearRegression().fit(np.random.rand(30, 16), np.random.rand(30) * 0.4),
             "features": list(range(16))}, f"{_TMP}/b.pkl")

from backend.fake_model import RandomRedshiftModel
joblib.dump(RandomRedshiftModel(0), f"{_TMP}/i.pkl")

# Point settings at temp models and reset model cache BEFORE the app is used
import backend.config, backend.model
backend.config.settings.BASELINE_PATH = f"{_TMP}/b.pkl"
backend.config.settings.IMAGE_MODEL_PATH = f"{_TMP}/i.pkl"
backend.model._baseline = None
backend.model._image = None

import backend.main


@pytest.fixture(scope="module")
def client():
    with TestClient(backend.main.app) as c:
        yield c


def _npy(shape):
    buf = io.BytesIO()
    np.save(buf, np.random.rand(*shape).astype(np.float32))
    buf.seek(0)
    return buf.read()


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_predict_image_only(client):
    r = client.post("/predict",
                    data={"ra": "180.0", "dec": "0.0"},
                    files={"file": ("c.npy", _npy((64, 64, 5)), "application/octet-stream")})
    assert r.status_code == 200
    body = r.json()
    assert "z" in body and "distance_gly" in body


def test_predict_image_and_tabular(client):
    tab = {"dered_u": 19.5, "dered_g": 18.0, "dered_r": 17.5, "dered_i": 17.0, "dered_z": 16.8,
           "expRad_r": 2.0, "deVRad_r": 1.5, "petroRad_r": 3.0, "petroR50_r": 1.2,
           "petroR90_r": 3.0, "fracDeV_r": 0.5}
    r = client.post("/predict",
                    data={"ra": "180.0", "dec": "0.0", "tabular": json.dumps(tab)},
                    files={"file": ("c.npy", _npy((64, 64, 5)), "application/octet-stream")})
    assert r.status_code == 200
    assert "z" in r.json()


def test_predict_wrong_shape_422(client):
    r = client.post("/predict",
                    data={"ra": "180.0", "dec": "0.0"},
                    files={"file": ("c.npy", _npy((32, 32, 5)), "application/octet-stream")})
    assert r.status_code == 422
