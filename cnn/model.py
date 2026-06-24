"""Photo-z CNN image branch.
TASK 01 -> inception ; TASK 02 -> build_cnn ; TASK 03 -> build_embedder.
Outputs a standalone z head + a 64-d `embedding` layer that feeds the fusion MLP head."""
from tensorflow.keras import layers as L, Model, Input

IMG_SHAPE = (64, 64, 5)
EMBED_DIM = 64


def inception(x, f1, f3r, f3, f5r, f5, fp, name):
    """4 parallel branches concatenated on the channel axis (see task notebook for the recipe):
    1x1 ; 1x1->3x3 ; 1x1->5x5 ; (3x3 maxpool stride 1)->1x1. Output channels = f1 + f3 + f5 + fp.
    The 1x1 reducers f3r/f5r shrink channels before the costly 3x3/5x5 convs."""
    # TODO (task 01)
    raise NotImplementedError


def build_cnn(input_shape=IMG_SHAPE, embed_dim=EMBED_DIM):
    """VGG stem (downsample 64->16) -> 3 inception modules (BN + MaxPool between) -> GAP
    -> Dense(128, relu) -> Dropout(0.3) -> Dense(embed_dim, name='embedding') -> Dense(1, name='z').
    Returns a keras Model. Use the inception() above."""
    # TODO (task 02)
    raise NotImplementedError


def build_embedder(cnn):
    """The frozen feature extractor for the fusion head:
    a Model from cnn.input to the 'embedding' layer's output."""
    # TODO (task 03)
    raise NotImplementedError
