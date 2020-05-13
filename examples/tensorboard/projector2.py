# Credit: https://stackoverflow.com/a/41177133/5854947

import os

from datetime import datetime

import numpy as np
import tensorflow as tf
import tensorboard as tb

tf.io.gfile = tb.compat.tensorflow_stub.io.gfile

from tensorboardX import SummaryWriter

vectors = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0], [1, 1, 1]])
metadata = ['001', '010', '100', '111']  # labels

log_dir = os.getenv("LOGDIR") or "logs/projector/" + datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)
with SummaryWriter(log_dir) as writer:
    writer.add_embedding(vectors, metadata)
