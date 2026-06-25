"""API contract tests for the v4 fusion stack.

Runs against the REAL artifacts under models/ (CI pulls them from GCS; locally they're staged
by `scripts/get_models.sh` / the dev setup). These check routing, validation and response shape
— not the model math. The app loads CNN + fusion + tabular stack + medians at startup (lifespan),
so a missing models/ dir surfaces here as a load error.
"""
import io
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

import backend.main

CROP = backend.main.settings.CROP          # 24
BANDS = backend.main.settings.IMG_SHAPE[-1]  # 5


@pytest.fixture(scope="module")
def client():
    with TestClient(backend.main.app) as c:   # triggers lifespan -> load_models()
        yield c


def _npy(shape):
    buf = io.BytesIO()
    np.save(buf, np.random.rand(*shape).astype(np.float32))
    buf.seek(0)
    return buf.read()


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert tuple(j["input_shape"]) == (CROP, CROP, BANDS)


def test_predict_image_only(client):
    r = client.post("/predict",
                    files={"file": ("c.npy", _npy((CROP, CROP, BANDS)), "application/octet-stream")})
    assert r.status_code == 200
    body = r.json()
    assert "z" in body and "distance_gly" in body


def test_predict_image_and_tabular(client):
    tab = {"dered_u": 19.5, "dered_g": 18.0, "dered_r": 17.5, "dered_i": 17.0, "dered_z": 16.8,
           "expRad_r": 2.0, "deVRad_r": 1.5, "petroRad_r": 3.0, "petroR50_r": 1.2,
           "petroR90_r": 3.0, "fracDeV_r": 0.5}
    r = client.post("/predict",
                    data={"ra": "180.0", "dec": "0.0", "tabular": json.dumps(tab)},
                    files={"file": ("c.npy", _npy((CROP, CROP, BANDS)), "application/octet-stream")})
    assert r.status_code == 200
    assert "z" in r.json()


def test_explain_image_only(client):
    r = client.post("/explain",
                    files={"file": ("c.npy", _npy((CROP, CROP, BANDS)), "application/octet-stream")})
    assert r.status_code == 200
    body = r.json()
    assert "redshift" in body and "heatmap" in body
    hm = body["heatmap"]
    assert len(hm) == CROP and len(hm[0]) == CROP          # CROP x CROP saliency
    assert all(0.0 <= v <= 1.0 for row in hm for v in row)  # normalized to [0,1]


def test_predict_wrong_bands_422(client):
    # wrong channel count (not a 5-band ugriz cutout) -> ValueError -> 422
    r = client.post("/predict",
                    files={"file": ("c.npy", _npy((CROP, CROP, 3)), "application/octet-stream")})
    assert r.status_code == 422


def test_predict_too_small_422(client):
    # smaller than the crop -> ValueError -> 422
    r = client.post("/predict",
                    files={"file": ("c.npy", _npy((CROP - 4, CROP - 4, BANDS)), "application/octet-stream")})
    assert r.status_code == 422
