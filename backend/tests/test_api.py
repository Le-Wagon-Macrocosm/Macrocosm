"""TASK 09: TestClient tests for GET / and POST /predict."""
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# TODO test_root
# TODO test_predict_batch  (np.zeros((3,64,64,5)).tolist() -> 200, 3 predictions)
# TODO test_predict_bad_shape  (32x32x5 -> 422)
