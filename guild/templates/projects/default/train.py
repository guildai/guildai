# This is a sample script that can be used to implement real model
# training. Refer to the comments below for more information.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse

import tensorflow as tf

def main():
    """Handle command line arguments."""

    args = _parse_args()
    model = _init_model(args)
    _train(model, args)

def _parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser()

    # TODO: Modify the arguments below as needed define the user
    # interface to your model. It's a good idea to expose any model
    # parameter that a user could modify without compromising model
    # interity. Use 'add_argument("--NAME", default=VALUE)' below for
    # each parameter rather than hard-coding them elsewhere in this
    # module.
    #
    parser.add_argument("--epochs", default=20, type=int)
    parser.add_argument("--batch-size", default=64, type=int)
    parser.add_argument("--learning-rate", default=0.01, type=float)

    return parser.parse_args()

def _init_model(args):
    """Initialize the model."""

    # TODO: Initialize your model here using one of the various
    # TensorFlow libraries:
    #
    # - Keras: https://goo.gl/3sKGa2
    # - TF Layers: https://goo.gl/6LcLTb
    # - Low level TensorFlow: https://goo.gl/zqjMvz
    #
    # Use values in 'args' for model parameters rather than hard-code
    # them.
    #
    # In this sample, we use a string to represent our model. It
    # trains fast!
    #
    return (
        "sample model (batch-size: {}, learning-rate: {})".format(
        args.batch_size, args.learning_rate)
    )

def _train(model, args):
    """Train the model."""

    # TODO: Replace with your model model training loop or fit
    # operation.
    #
    for i in range(args.epochs):
        print("Training %s: epoch %i" % (model, i + 1))
        import time; time.sleep(0.05) # Simulate fast training!

if __name__ == "__main__":
    main()
