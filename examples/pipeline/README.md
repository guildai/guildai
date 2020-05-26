# Guild Example: `pipeline`

This example shows a basic data processing pipeline. It is adapted
from [*Transfer Learning For Computer Vision
Tutorial*](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html).

- [guild.yml](guild.yml) - Project Guild file
- [prepare.py](prepare.py) - Script to prepare images for training
- [train.py](train.py) - Script to train model
- [util.py](util.py) - Shared functions

Operations:

- `prepare-images` - prepare images for training; required for
  training
- `train` - train model on prepared images
- `pipeline` - run an end-to-end pipeline with various training
  scenarios

## Setup

To run the demo, change to this directory and create a new environment.

    $ guild init -l

The `-l` option tells Guild to use a resource cache that's local,
rather than shared. This ensures that downloaded image datasets are
removed when you remove the example environment `venv`.

## Prepare Images

Start by prepraing the images for training.

    $ guild run prepare-images

This generates some `pth` files that are read by the `train`
operation. List the generated files using `ls`.

    $ guild ls

The script also generates a plot of sample prepared images. Open the
image to review a handful of prepared images.

    $ guild open -p prepared-samples.png

## Train Model (Fine Tune)

Next, run a training run with a single epoch. This runs quickly to let
you review the results.

    $ guild run train epochs=1

Review the default flags. These flags are imported from the training
script according to the configuration in[guild.yml](guild.yml).

Press `Enter` to train a model.

Guild runs [`train.py`](train.py), which is defined as the `main` spec
in [`guild.yml`](guild.yml). Flags are set as global variables. This
allows the script to be run with minimial-to-no modifications. In fact
the only modifications to the [original
code](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
is to use variables to define train behavior. These variables are
exposed to users as flags through Guild.

The training run generates a saved model along with
`predict-samples.png`, which is a sample of images and their predicted
classes. View the generated files using `ls`.

    $ guild ls

## Train Model (Freeze Layers)

Run `train` again but using frozen layers.

    $ guild run train freeze_layers=yes epochs=1

This corresponds to the `model_conv` training in the original
script. [`train.py`](train.py) is modified to only generate one
model. Frozen layers are controlled by the `freeze_layers` global
variable, which is exposed as a flag by Guild.

You can generate one of each model this way:

    $ guild run train freeze_layers=[yes,no]

Guild runs `train` once for each value of `freeze_layers`.

`train.py` specializes in training one model. Guild specializes in
running `train.py` with different parameters (flag values). This lets
you experiment with different training scenarios without modifying
`train.py`. As a matter of "best practices", the more configurable you
make a script, more you can experiment with it using tools like Guild.

## Pipeline

To run a full pipeline, which generates several trained models across
a range of hyperparamers, use the `pipeline` operation. `pipeline`
accepts a single `epochs` flag but otherwise defines its own set of
hyperparameter ranges for `train`.

To run `pipeline` with 5 epochs, use:

    $ guild run pipeline epochs=5

This will take some time to complete.

As Guild trains the models, you can watch the training progress by
running Guild commands from other terminals.

View runs, including staged runs, in-progress runs, and completed
runs:

    $ guild runs

Compare run performance (use the arrow keys to navigate, press `r` to
refresh the runs display, `q` to exit the program, and `?` for help):

    $ guild compare

View runs in TensorBoard:

    $ guild tensorboard

Explore the various tabs in TensorBoard. Note that Guild provides
images and hyperparameters in TensorBoard for each run.
