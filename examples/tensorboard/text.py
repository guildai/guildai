"""Ref: https://www.tensorflow.org/api_docs/python/tf/summary/text
"""

import argparse

import tensorflow as tf

p = argparse.ArgumentParser()
p.add_argument("--logdir", default="/tmp/text_demo")
args = p.parse_args()

print("Writing logs to %s" % args.logdir)

writer = tf.summary.create_file_writer(args.logdir)
with writer.as_default():
    tf.summary.text("color", tf.convert_to_tensor("blue"), 10)
    tf.summary.text(
        "text",
        tf.convert_to_tensor(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed venenatis, "
            "nisl in lacinia placerat, tortor neque blandit erat, ut auctor dui dolor "
            "quis elit."
        ),
        10,
    )
    tf.summary.text("color", tf.convert_to_tensor("green"), 20)
    tf.summary.text(
        "text",
        tf.convert_to_tensor(
            "Vestibulum a tellus accumsan, posuere tellus sed, volutpat elit. Ut "
            "venenatis in massa ac scelerisque. Ut in risus ut turpis facilisis "
            "maximus."
        ),
        20,
    )
    tf.summary.text("color", tf.convert_to_tensor("red"), 30)
    tf.summary.text(
        "text",
        tf.convert_to_tensor(
            "Aenean malesuada risus non laoreet efficitur. Maecenas sit amet laoreet "
            "sem, ac eleifend augue. Suspendisse potenti. Morbi euismod tempor gravida."
        ),
        30,
    )
    writer.flush()
