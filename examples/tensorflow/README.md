# Guild Example: `tensorflow`

This example illustrates a simple TensorFlow training script.

Highlights:

- Train and validate are separate operations to illustate dependencies
- Script uses `argparse` to provide a command line interface
- Required data set files are defined as dependencies

- [guild.yml](guild.yml) - Project Guild file
- [mnist.py](mnist.py) - Training script with support for validation

Operations:

- [`train`](#train) - trains a model
- [`validate`](#validate) - validatest a trained model

## `train`

Use to train an MNIST classifier. This is the standard logistic
regression with softmax classifier in TensorFlow.

    $ guild run train epochs=5

Here's the definition of `train`:

``` yaml
train:
  description: Train MNIST classifier
  main: mnist
  default: yes
  requires:
    path: data
    default-unpack: no
    sources:
      - url: http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz
      - url: http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz
      - url: http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz
      - url: http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz
  flags-import:
    - batch_size
    - epochs
  compare:
    - loss step as step
    - loss as train_loss
    - acc as train_acc
```

- ``default: yes`` indicates that the operation is the default. You
  can run the default operation without specifying it. E.g. ``guild
  run`` is equivalent to ``guild run train``.
