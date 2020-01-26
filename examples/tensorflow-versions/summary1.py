# Uses TF 1.x summary writer to log a scalar.
#
# Guild should extend the logged data with system scalars.

import sys

import tensorflow as tf

assert len(sys.argv) >= 2, "usage: summary1.py LOGDIR"

writer = tf.summary.FileWriter(sys.argv[1])

def scalar_summary(tag, val):
    return tf.Summary(value=[tf.Summary.Value(tag=tag, simple_value=val)])

writer.add_summary(scalar_summary("x", 1.0), 1)
writer.add_summary(scalar_summary("x", 2.0), 2)
writer.add_summary(scalar_summary("x", 3.0), 3)
writer.close()
