"""Placeholder image -> redshift model. Same `.predict` interface the real CNN will expose,
so no backend code changes when the real (fused) model is swapped in. NOT a task to implement."""
import numpy as np
import tensorflow as tf

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



@tf.keras.utils.register_keras_serializable()
def mdn_loss(num_gaussians=5):
    """NLL loss over MDN output (pi, mu, sigma) vs scalar target."""
    @tf.keras.utils.register_keras_serializable()
    def loss(y_true, y_pred):
        pi  = y_pred[:, :num_gaussians]                          # mixture weights
        mu  = y_pred[:, num_gaussians:2*num_gaussians]           # means
        sig = y_pred[:, 2*num_gaussians:]                        # std devs

        y_true = tf.expand_dims(y_true, 1)                       # (batch,1) for broadcasting

        # gaussian probability for each component
        norm = tf.math.log(pi + 1e-8) - 0.5 * tf.math.log(
                2 * np.pi * sig**2 + 1e-8
               ) - 0.5 * ((y_true - mu) / (sig + 1e-8))**2      # (batch, num_gaussians)

        # log-sum-exp for numerical stability
        nll = -tf.reduce_logsumexp(norm, axis=1)                 # (batch,)
        return tf.reduce_mean(nll)
    return loss
