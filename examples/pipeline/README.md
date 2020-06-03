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

Activate the environment:

    $ source guild-env

## Prepare Images

Start by prepraing the images for training.

    $ guild run prepare-images

This runs the underlying [`prepare.py`](prepare.py), which downloads a
sample data set of images and prepares PyTorch `DataLoader` objects to
serve them to downstream training runs. The script saves the loaders
in `pth` files.

List the generated files using `ls`.

    $ guild ls

Here are the files associated with the run:

```
<run dir>:
  data/
  data/hymenoptera_data/
  prepare-samples.png
  train.pth
  val.pth
```

Note `train.pth` and `val.pth` - these are saved data loaders. These
files, along with `data`, are used later by `train` runs. When you
generate a data set using `prepare-images`, you can reuse those files
for multiple training runs without regenerating them.

The script also generates a plot of sample prepared images. Open the
image to review a handful of prepared images.

    $ guild open -p prepare-samples.png

## Train Model (Fine Tune)

The `train` operation requires files from `prepare-images` above. This
is referred to in Guild as a *dependency*. The dependency is defined
in [`guild.yml`](guild.yml) under the `requires` attribute of the
`train` operation:

``` yaml
train:
  ...
  requires:
    - operation: prepare-images
      name: images
```

This tells Guild to look for a `prepare-images` run and *create links
to its files in the `train` run directory.* When you run `train`,
required files are available within the current working directory.

Run `train` with a single epoch (we're not interested in high accuracy
for this demo):

    $ guild run train epochs=1

Guild prompts you with a preview message showing the run flag
values.

```
You are about to run train
  epochs: 25
  freeze_layers: no
  images: <run ID>
  lr: 0.001
  lr_decay_epochs: 7
  lr_decay_gamma: 0.1
  momentum: 0.9
Continue? (Y/n)
```

Note the `images` flag. This indicates the run used to satisfy the
`images` dependency defined for `train`. By default, Guild selects the
most recent non-error run for the required operation. You can select a
different run by specifying the run ID as a flag assignment.

Press `Enter` to start the run.

Before Guild starts the [underlying script](train.py) for `train`, it
*resolves all dependencies defined for the operation*. If Guild cannot
resolve all dependencies, it exits with an error message prior to
running the script.

In this case, Guild resolves the `images` dependency by creating links
to its files in the `train` run directory.

Wait for the operation to finish and list its files:

    $ guild ls

Note that `train` generates `model.pth`, which is the saved trained
model. It also generates `predict-images.png`, which contains a sample
of prediction results.

Note also that the `train` run directory contains files from
the selected `prepare-images` run:

```
  data/
  prepare-samples.png
  train.pth
  val.pth
```

You can verify that these files are links to the applicable
`prepare-images` run directory.

> Hint: an easy way to explore a run directory is to use `guild open`,
> which opens the latest run directory in your local file explorer.

## Train Model (Freeze Layers)

Run `train` again using frozen layers.

    $ guild run train freeze_layers=yes epochs=1

This corresponds to [*ConvNet as fixed feature
extractor*](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html#convnet-as-fixed-feature-extractor)
in the PyTorch tutorial. Note that [`train.py`](train.py) is modified
to only generate one model rather than multiple models like the
tutorial. Frozen layers are controlled by the `freeze_layers` global
variable, which is exposed as a flag.

You can generate one of each model this way:

    $ guild run train freeze_layers=[yes,no]

Guild runs `train` once for each value of `freeze_layers`.

As with the first `train` run, each subsequent train run uses output
from a `prepare-images` run. This saves time and disk space.

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
