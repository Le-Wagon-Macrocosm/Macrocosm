"""Grad-CAM for the v4 fusion photo-z stack, w.r.t. the input image.

The fusion model has no image input — it's an MLP+MDN over [3 base | 16 mask | 64 CNN embedding].
So we compose ONE differentiable graph and back-prop the redshift to the image's conv features:

    image --CNN--> [ last conv feature map | 'embedding' (64) ]
    fusion_vec = concat([ base(3), mask(16), embedding(64) ])      # base/mask are CONSTANT w.r.t. image
    z_log1p    = E[ MDN ]  =  sum(pi * mu)   over the fusion output
    heatmap    = Grad-CAM( d z_log1p / d (last conv map) )

Because the tabular base preds + mask don't depend on the image, the gradient flows only
image -> conv -> embedding -> fusion -> z, so the heatmap reflects *where in the cutout* the model
reads the redshift from. The displayed redshift is the MDN point estimate (mu of the top component).
"""
import numpy as np
import tensorflow as tf

from .model import get_models, embedder, tabular_base_preds, mdn_point


def _last_conv_layer(cnn):
    """Last layer with a rank-4 (spatial) output — the inception block right before global pooling."""
    for layer in reversed(cnn.layers):
        try:
            if len(layer.output.shape) == 4:
                return layer
        except Exception:
            continue
    raise ValueError("No 4D (conv) feature map found in the CNN.")


def explain(images, X16=None, mask=None, image_only=False):
    """images: (1,CROP,CROP,5) preprocessed (p99). X16/mask: (16,) tabular or None (-> absent).
    image_only=True -> Grad-CAM on the CNN's own MDN head (no tabular/fusion), matching the
    image-only /predict path; else the fusion composite. Returns {'redshift', 'heatmap' (CROP,CROP) in [0,1]}."""
    _stack, cnn, fusion = get_models()
    conv_layer = _last_conv_layer(cnn)
    x = tf.cast(images, tf.float32)

    if image_only:
        # back-prop the CNN's own MDN redshift to its last conv map (no tabular branch)
        grad_model = tf.keras.Model(cnn.input, [conv_layer.output, cnn.output])
        with tf.GradientTape() as tape:
            conv_out, raw = grad_model(x, training=False)    # (1,h,w,C), (1,15)
            tape.watch(conv_out)
            K = raw.shape[-1] // 3
            pi, mu = raw[:, :K], raw[:, K:2 * K]
            z_log1p = tf.reduce_sum(pi * mu, axis=-1)[0]     # differentiable expected log1p(z)
    else:
        # base preds + mask are CONSTANT w.r.t. the image -> bake them in as fixed tensors
        if X16 is None:
            X16 = np.full((1, 16), np.nan, "float32")
            mask = np.zeros((1, 16), "float32")
        base, m = tabular_base_preds(X16, mask)              # (1,3), (1,16)
        base_t, mask_t = tf.constant(base, tf.float32), tf.constant(m, tf.float32)
        grad_model = tf.keras.Model(cnn.input, [conv_layer.output, embedder().output])
        with tf.GradientTape() as tape:
            conv_out, emb = grad_model(x, training=False)    # (1,h,w,C), (1,64)
            tape.watch(conv_out)
            fvec = tf.concat([base_t, mask_t, emb], axis=1)  # (1,83)
            raw = fusion(fvec, training=False)               # (1,15) = [pi(5), mu(5), sigma(5)]
            K = raw.shape[-1] // 3
            pi, mu = raw[:, :K], raw[:, K:2 * K]             # pi already softmax (mdn_pi head)
            z_log1p = tf.reduce_sum(pi * mu, axis=-1)[0]     # differentiable expected log1p(z)

    grads = tape.gradient(z_log1p, conv_out)
    if grads is None:
        raise ValueError("Grad-CAM gradient is None — conv map not on the path to the output.")

    pooled = tf.reduce_mean(grads, axis=(0, 1, 2))           # (C,)  importance per channel
    cam = tf.reduce_sum(conv_out[0] * pooled, axis=-1)       # (h,w)
    cam = tf.nn.relu(cam)                                    # keep positive contributions
    cam = cam - tf.reduce_min(cam)
    cam = cam / (tf.reduce_max(cam) + 1e-8)                  # -> [0,1]

    H, W = int(x.shape[1]), int(x.shape[2])
    cam = tf.image.resize(cam[None, ..., None], [H, W], method="bilinear")
    heatmap = tf.squeeze(cam).numpy().astype("float32")      # (H,W)

    z = float(np.expm1(mdn_point(raw.numpy()))[0])           # displayed point estimate (expm1 of mu*)
    return {"redshift": z, "heatmap": heatmap}
