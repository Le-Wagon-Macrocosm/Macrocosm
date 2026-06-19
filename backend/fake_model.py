"""Placeholder image -> redshift model. Same `.predict` interface the real CNN will expose,
so no backend code changes when the real (fused) model is swapped in. NOT a task to implement."""
import numpy as np


class RandomRedshiftModel:
    input_shape = (64, 64, 5)

    def __init__(self, seed: int = 0, zmin: float = 0.02, zmax: float = 0.35):
        self.rng = np.random.default_rng(seed)
        self.zmin, self.zmax = zmin, zmax

    def predict(self, X):
        """X: (n,S,S,5) or (S,S,5) -> np.ndarray (n,) of random z in [zmin, zmax]."""
        X = np.asarray(X)
        n = 1 if X.ndim == 3 else len(X)
        return self.rng.uniform(self.zmin, self.zmax, size=n).astype("float32")
