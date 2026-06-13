"""Minimal training entrypoint with MLflow tracking (Keras).

Run: `make train`.  The MLflow + metrics wiring is complete; the data loading
and the model architecture are TODOs.

Tracking backend: set $MLFLOW_TRACKING_URI (Colab -> a Drive path or your VPS
server), otherwise runs are written to ./mlruns (lost when Colab resets).
"""
import os

import numpy as np
import mlflow
import mlflow.tensorflow
from tensorflow import keras


# --- photo-z metrics (the numbers we actually care about) ------------------
def photoz_metrics(z_spec, z_pred, outlier_thresh=0.15):
    dz = (np.asarray(z_pred) - np.asarray(z_spec)) / (1.0 + np.asarray(z_spec))
    return {
        "sigma_mad":    float(1.4826 * np.median(np.abs(dz - np.median(dz)))),
        "bias":         float(np.median(dz)),
        "outlier_rate": float(np.mean(np.abs(dz) > outlier_thresh)),
    }


def load_dataset():
    # TODO: load frozen sample_v1 from GCS  ->  images (N,64,64,5) + redshift z
    # TODO: same preprocessing as serving (arcsinh stretch, normalize), 70/15/15 split
    raise NotImplementedError("load the frozen dataset from GCS")


def build_model():
    # TODO: small CNN on (64,64,5); regress log1p(z) for numerical stability
    raise NotImplementedError("define the CNN")


def main():
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns"))
    mlflow.set_experiment("photo-z")
    mlflow.tensorflow.autolog()          # auto-logs params / metrics / the Keras model

    (X_train, y_train), (X_val, y_val) = load_dataset()   # y = log1p(z)

    with mlflow.start_run(run_name="cnn-baseline"):
        mlflow.log_params({"model": "cnn", "bands": "ugriz", "target": "log1p_z",
                           "batch": 64, "lr": 1e-3})

        model = build_model()
        model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="huber")
        model.fit(
            X_train, y_train, validation_data=(X_val, y_val),
            epochs=30, batch_size=64,
            callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)],
        )

        # custom photo-z metrics on the validation set (undo the log1p target)
        z_val  = np.expm1(y_val)
        z_pred = np.expm1(model.predict(X_val).ravel())
        metrics = photoz_metrics(z_val, z_pred)
        mlflow.log_metrics(metrics)
        print(metrics)


if __name__ == "__main__":
    main()
