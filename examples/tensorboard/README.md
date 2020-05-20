# Guild Example: `tensorboard`

This example shows various TensorBoard integrations. Examples are
copied from [*Get started with
TensorBoard*](https://www.tensorflow.org/tensorboard/get_started).

Project files:

- [guild.yml](guild.yml) - Project Guild file
- [loss_scalar.py](loss_scalar.py) - Script for `loss-scalar` operation
- [custom_scalar.py](custom_scalar.py) - Script for `custom-scalar` operation
- [images.py](images.py) - Script for `images` operation
- [graphs.py](graphs.py) - Script for `graphs` operation
- [hparams.py](hparams.py) - Script for `hparams` operation
- [projector.py](projector.py) - Script for `projector` operation
- [projector2.py](projector2.py) - Script for `projector2` operation
- [audio.py](audio.py) - Script for `audio` operation
- [pr_curve.py](pr_curve.py) - Script for 'pr-curve' operation

To run the examples, first create an environment.

    $ cd examples/tesnorboard
    $ guild init

Press `Enter` to create a virtual environment that is configured with
the required Python packages for this example.

Activate the environment:

    $ source guild-env

Run any of operations below. Each operation implements one of the
examples from [*Get started with
TensorBoard*](https://www.tensorflow.org/tensorboard/get_started).

- `loss-scalar` - Implementation of part 1 of [*TensorBoard Scalars:
  Logging training metrics in
  Keras*](https://www.tensorflow.org/tensorboard/scalars_and_keras)
- `custom-scalar` - Implementation of part 2 of [*TensorBoard Scalars:
  Logging training metrics in
  Keras*](https://www.tensorflow.org/tensorboard/scalars_and_keras)
- `images` - Implementation fo [*Displaying image data in
  TensorBoard*](https://www.tensorflow.org/tensorboard/image_summaries)
- `graphs` - Implementation of [*Examining the TensorFlow
  Graph*](https://www.tensorflow.org/tensorboard/graphs)
- `hparams` - Implementation of [*Hyperparameter Tuning with the
  HParams
  Dashboard*](https://www.tensorflow.org/tensorboard/hyperparameter_tuning_with_hparams) -
  (see [Hyperparameter Tuning](#hyperparameter-tuning) below for more
  on this operation)
- `hparams-grid-search` - Grid search of `hparams` operation over the
  range used in the TensorBoard hyperparameter tuning example
- `hparams-optimize` - Bayesian optimization of `hparams` operation
  using Gaussian Processes
- `projector` - [*Visualizing Data using the Embedding Projector in
  TensorBoard*](https://www.tensorflow.org/tensorboard/tensorboard_projector_plugin)
  (this demo does not work as expected - see [Projector
  Demo](#projector-demo) below for details)
- `projector2` - Alternative projector demo
  ([credit](https://stackoverflow.com/a/41177133/5854947)) using
  [`tensorboardX`](https://github.com/lanpa/tensorboardX) to write
  embedding summaries (this operation is an alternative to `projector`
  that works as expected - seee [Projector Demo](#projector-demo)
  below for details)
- `audio` - TensorBoard audio demo
  ([credit](https://github.com/tensorflow/tensorboard/blob/master/tensorboard/plugins/audio/audio_demo.py))
- `pr-curve` - TensorBoard PR Curve demo
  ([credit](https://github.com/tensorflow/tensorboard/blob/master/tensorboard/plugins/pr_curve/pr_curve_demo.py))

To run one of these operations, use:

    $ guild run <operation>

Review the default flags and press `Enter` to run the operation.

## Hyperparameter Tuning

The implementation of the [TensorBoard hyperparameter tuning
example](https://www.tensorflow.org/tensorboard/hyperparameter_tuning_with_hparams)
highlights one of Guild's primary design differentiators: *the
separation of model training code from hyperparameter tuning code*.

The Guild implementation in [hparams.py](hparams.py) is free from any
hyperparameter tuning code. The [TensorBoard
example](https://github.com/tensorflow/tensorboard/blob/master/docs/hyperparameter_tuning_with_hparams.ipynb)
combines both model training code and hyperparameter tuning code.

There are advantages to Guild's approach:

- Code that is free from hyperparameter tuning related code is simpler
  and easier to read and therefore easier debug, improve, etc.

- Moving hyperparameter code outside of model training code lets you
  run different tuning operations without changing model code.

- Separating hyperparameter tuning concerns lets you use different
  tuning frameworks to optimize your models.

Guild automatically manages TensorBoard hparam summaries for all
runs. This lets you use TensorBoard's **HPARAMS** plugin with any run,
whether it was designed for hyperparameter tuning or not. This works
for runs implemented in frameworks other then TensorFlow - and even in
languages other than Python.

To run tuning operations on `hparams`, see `hparams-grid-search` and
`hparams-optimize` operations.

## Projector Demo

Google's [projector
demo](https://www.tensorflow.org/tensorboard/tensorboard_projector_plugin)
does not work as expected with Guild. This demo requires that
TensorBoard's log directory be specified as the demo directory rather
than as the demo directory parent. Guild arranges the TensorBoard log
directory as a container of runs. However, this demo does not work
with this arrangement.

See [this issue on
GitHub](https://github.com/tensorflow/tensorboard/issues/3629) for
status on this.

The `projector` operation uses Google's demo code as
provided. Therefore the `projector` operation does not work as
expected: when you run `guild tensorboard`, any associated runs will
not display the expected embeddings.

The `projector2` operation, however, does show embeddings per run as
expected. This is a simplified demo that uses `tensorboardX` to write
embedding summaries.
