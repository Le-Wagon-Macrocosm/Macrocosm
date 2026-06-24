from backend.features import preprocess_image
from backend.model import load_models, get_models, predict_z

import numpy as np

import tensorflow as tf
import numpy as np



def predict_z_mdn(predictions):
    """
    mdn output: (6000, 15) — 6000 spatial positions, 5 gaussians × 3 params
    Strategy: mean-pool across spatial dim first, then decode MDN
    """
    def decode_mdn_head(raw):
        # raw: (6000, 15)

        # Step 1 — collapse spatial dimension → (1, 15)
        raw_pooled = tf.reduce_mean(raw, axis=0, keepdims=True)

        # Step 2 — slice the 5 gaussian components
        n = raw_pooled.shape[-1] // 3      # = 5

        pi_logits = raw_pooled[:, :n]      # (1, 5)
        mu        = raw_pooled[:, n:2*n]   # (1, 5)
        # log_sigma = raw_pooled[:, 2*n:]  # (1, 5) — available if needed

        # Step 3 — softmax logits → mixture weights
        pi = tf.nn.softmax(pi_logits, axis=-1)

        # Step 4 — weighted mean redshift
        z = tf.reduce_sum(pi * mu, axis=-1)   # (1,)
        return z, pi

    z1, pi1 = decode_mdn_head(predictions['mdn1_out'])
    z2, pi2 = decode_mdn_head(predictions['mdn2_out'])

    # Confidence-weighted combination of both heads
    confidence1 = tf.reduce_max(pi1, axis=-1)
    confidence2 = tf.reduce_max(pi2, axis=-1)
    total = confidence1 + confidence2 + 1e-8

    z_hat = (confidence1 * z1 + confidence2 * z2) / total

    return tf.cast(z_hat, tf.float64)


def explain(preprocess_img: list):
    # 1. Load model and input
    baseline, image = get_models()

    # 2. Find last Conv2D layer
    target_layer_name = None
    for layer in image.layers:
        if isinstance(layer, tf.keras.layers.Conv2D):
            target_layer_name = layer.name

    if not target_layer_name:
        raise ValueError("No Conv2D layer found in the model.")

    target_layer = image.get_layer(target_layer_name)

    # 3. Intermediate model: outputs [last_conv_activations, predictions]
    grad_model = tf.keras.Model(
        inputs=[image.input],
        outputs=[target_layer.output, image.output]
    )

    # 4. Forward pass under GradientTape
    #    Must cast input to float32 and watch conv_output explicitly —
    #    tape only auto-watches tf.Variables, not intermediate tensors
    preprocess_img = tf.cast(preprocess_img, tf.float32)

    with tf.GradientTape() as tape:
        conv_output, predictions = grad_model(preprocess_img)
        tape.watch(conv_output)                      # <-- required
        z_hat = predict_z_mdn(predictions)           # scalar float64
        z_scalar = tf.cast(z_hat[0], tf.float32)    # tape needs float32

    # 5. Gradients of redshift prediction w.r.t. conv feature maps
    #    grads shape: same as conv_output → (6000, H_conv, W_conv, C)
    grads = tape.gradient(z_scalar, conv_output)

    if grads is None:
        raise ValueError(
            "Gradients are None — conv_output is not on the gradient path. "
            "Check that tape.watch(conv_output) is inside the tape block."
        )

    # 6. Grad-CAM formula
    #    Global average pool gradients over spatial dims → (C,)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))   # (C,)

    #    Weight each feature map channel by its pooled gradient
    #    conv_output: (6000, H_conv, W_conv, C)
    #    pooled_grads[tf.newaxis, tf.newaxis, tf.newaxis, :] → broadcasts over spatial
    cam = tf.reduce_sum(
        conv_output * pooled_grads[tf.newaxis, tf.newaxis, tf.newaxis, :],
        axis=-1
    )                                                       # (6000, H_conv, W_conv)

    # 7. Pool over the 6000 spatial positions → (H_conv, W_conv)
    cam = tf.reduce_mean(cam, axis=0)

    # 8. Normalize
    cam = tf.nn.relu(cam)                          # discard negative contributions
    cam = cam - tf.reduce_min(cam)                 # shift floor to 0
    cam = cam / (tf.reduce_max(cam) + 1e-8)       # scale to [0, 1]

    # 9. Upsample to original input spatial size
    #    tf.image.resize expects (batch, H, W, channels)
    H, W = preprocess_img.shape[1], preprocess_img.shape[2]

    cam_resized = tf.image.resize(
        tf.reshape(cam, (1, cam.shape[0], cam.shape[1], 1)),
        size=[H, W],
        method=tf.image.ResizeMethod.BILINEAR
    )
    cam_resized = tf.squeeze(cam_resized).numpy()  # (H, W)

    return {
        "redshift": float(z_scalar.numpy()),
        "heatmap": cam_resized                     # (H, W) float32 array in [0, 1]
    }
