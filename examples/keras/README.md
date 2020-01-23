# Guild Example: `keras`

This example shows how Guild works with Keras scripts.

- [guild.yml](guild.yml) - Project Guild file
- [mnist_mlp.py](mnist_mlp.py) - Copy of Keras
  [example](https://github.com/keras-team/keras/blob/master/examples/mnist_mlp.py)

Operations:

- [`mlp-mnist:train`](#mlp-mnisttrain) - Train MLP on MNIST

## Setup

Create a virtual environment for the project:

    $ cd examples/keras
    $ guild init

This installed Keras and TensorFlow.

Active the environment:

    $ source guild-env

## `mlp-mnist:train`

This operation runs [mnist_mlp.py](mnist_mlp.py).

It defines both flags in order to provide a description and default
values.

Guild provides special support for Keras scripts. The support includes
automatic configuration of output scalars with the correct patterns.

Guild implicitly uses these patterns to configure output scalars for
Keras scripts:

- `Epoch (?P<step>[0-9]+)`
- ` - ([a-z_]+): (\value)`

To start the operation, run:

    $ guild run mlp-mnist:train

Note that Guild uses the default flag values defined in
[guild.yml](guild.yml).

Press `Enter` to start the operation.

When the operation completes, verify that the correct scalars are
captured:

    $ guild runs info

Alternative, confirm the results in TensorBoard:

    $ guild tensorboard
