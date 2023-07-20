import tensorflow as tf

attrs = tf.summary.create_file_writer(".", filename_suffix=".attrs")

with attrs.as_default():
    tf.summary.scalar('loss', 0.345, step=1)
    ##tf.summary.text("model", "cnn", step=0)
    attrs.flush()
