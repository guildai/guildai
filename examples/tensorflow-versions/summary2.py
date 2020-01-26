# Uses TF 2.x summary writer to log a scalar.
#
# Guild should extend the logged data with system scalars.

import sys

import tensorflow as tf

assert len(sys.argv) >= 2, "usage: summary1.py LOGDIR"

writer = tf.summary.create_file_writer(sys.argv[1])

with writer.as_default():
    tf.summary.scalar("x", 1.0, 1)
    tf.summary.scalar("x", 2.0, 2)
    tf.summary.scalar("x", 3.0, 3)

writer.close()
