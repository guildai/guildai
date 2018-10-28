# Guild AI

[![CircleCI](https://circleci.com/gh/guildai/guildai.svg?style=shield)](https://circleci.com/gh/guildai/guild)
[![PyPI version](https://badge.fury.io/py/guildai.svg)](https://badge.fury.io/py/guildai)

This is the source repository for Guild AI.

Guild AI is a Python application that that streamlines TensorFlow and
Keras deep learning development. It's released under the Apache 2 open
source license.

- **[Latest release on PyPI](https://pypi.python.org/pypi/guildai)**
- **[Guild AI website](https://www.guild.ai)**
- **[Documentation](https://www.guild.ai/docs/)**
- **[Open issues](https://github.com/guildai/guildai/issues)**

Highlights:

- Automatically track training experiments
- Compare model performance at-a-glance
- Visualize training results with TensorBoard
- Seamless integration with Keras models
- Model packaging and distribution
- Train on EC2 and backup to S3

## Requirements

- Linux or Mac OS/X
- Python 2.7 or 3 with `pip` and `virtualenv`
- TensorFlow

## Install Guild AI

To install Guild AI with pip, run:

``` bash
pip install guildai
```

If you already have Guild AI installed, you can upgrade it to the
latest release using:

``` bash
pip install guildai --upgrade
```

For detailed install instructions, see [Install Guild
AI](https://www.guild.ai/install).

<a id="task-runner-example">

## Task runner example

Guild AI is used to automate TensorFlow training. In this example, we
create simple project and train a model, capturing run results as
experiments.

Before proceeding, verify the following:

- Guild AI is installed
- TensorFlow is installed (see [Install
  TensorFlow](https://www.tensorflow.org/install/) for assistance)

Create a sample project:

``` bash
mkdir sample-project
cd sample-project
wget https://raw.githubusercontent.com/guildai/examples/master/mnist/intro.py
```

Add the following Guild file to the project as
`sample-project/guild.yml`:

``` yaml
- model: sample
  description: A sample model (MNIST logistic regression)
  operations:
    train:
      description: Train the model
      main: intro
      flags:
        epochs:
          description: Number of epochs to train
          default: 1
```

Save you changes to `guild.yml` and verify that the sample project
contains these two files:

- `intro.py`
- `guild.yml`

View available project operations by running:

``` bash
guild operations
```

View project help:

``` bash
guild help
```

Press `q` to exit help.

Run the sample `train` operation:

``` bash
guild run train
```

Press `Enter` to continue.

The sample model trains in a few seconds.

List runs:

``` bash
guild runs
```

Runs are file system directories that contain run metadata and
generated output. Each run represents an experiment and is
automatically generated with the `run` command.

Run `train` again, but with more training:

``` bash
guild run train epochs=5
```

Compare run performance:

``` bash
guild compare
```

Note that the run with more training has a higher accuracy.

Feel free to experiment with other Guild commands (see below).

View information for the latest run:

``` bash
guild runs info
```

List files from most recent run:

``` bash
guild ls
```

View runs with Guild View:

``` bash
guild view
```

Note that you must quit Guild View by pressing `Ctrl-C` in the console
to return to a command prompt.

View runs with TensorBoard:

``` bash
guild tensorboard
```

Note that as with Guild View you must quit TensorBoard by pressing
`Ctrl-C` in the console to return to a command prompt.

You may optionally delete the runs by running:

``` bash
guild runs rm -o sample:train
```

For a complete list of commands, see [Commands](http://www.guild.ai/docs/commands/).

For a more in-depth example, see [Guild AI
introduction](https://www.guild.ai/docs/intro/).

## Package example

Guild package are standard Python packages that contain Guild
files. You generate them using the `package` command. Distribute
packages to colleauges to share your projects. In this example, we
create a package for the sample project created in the previous
section (see above).

Note that the steps below must be run after completing the previous
section [Task runner example](#task-runner-example).

Add the following to the project Guild file
(`sample-project/guild.yml`):

``` yaml
- package: sample
  version: 1.0
```

Save you changes to `guild.yml`.

From the `sample-project` directory, create a Python package:

``` bash
guild package
```

Guild creates `dist/sample-1.0-py2.py3-none-any.whl`. You can
distribute this file to colleagues to share your project.

To simulate how your colleagues would use your package, follow the
steps below.

Create a temporary Python virtual environment:

``` bash
virtualenv /tmp/sample-project-test
```

Activate the environment:

``` bash
source /tmp/sample-project-test/bin/activate
```

The activated environment does not share packages with the system. You
must install required packages, just as if you were a new user.

Install Guild AI and TensorFlow into the environment:

``` bash
pip install guildai tensorflow
```

Install `dist/sample-1.0-py2.py3-none-any.whl` into the environment:

``` bash
pip install dist/sample-1.0-py2.py3-none-any.whl
```

Change out of the `sample-project` directory (this ensures that you do
not see operations in the project directory):

``` bash
cd ~
```

List available operations:

``` bash
guild operations
```

You see the `train` operation available from the installed `sample`
package.

```
sample/sample:train  Train the model
```

The value `sample/sample:train` means that the model and its
operations are defined in the installed `sample` package.

Train the model:

``` bash
guild run sample:train
```

Runs that are generated in an activated virtual environment are stored
within the environment directory. Environments are useful for
isolating both installed packages and runs.

All of the Guild commands above apply to runs created from packaged
models.

When you are done experimenting with the installed package, feel free
to deactivate the environment and delete the temporary directory:

``` bash
deactivate
rm -rf /tmp/sample-project-test
```

Note that deleting `/tmp/sample-project-test` deletes all runs that
were generated when the environment was active.

## Learn more

For a more in-depth example, see [Guild AI
introduction](https://www.guild.ai/docs/intro/).

The examples above illustrate two core applications of Guild AI:

- Automate TensorFlow workflow by running operations
- Package and distribute models with operation support

Guild AI supports a number of other useful features, including:

- [Train remotely on EC2](https://www.guild.ai/docs/guides/train-on-ec2/)
- [Backup runs to S3](https://www.guild.ai/docs/guides/backup-to-s3/)

Guild AI supports an ever-growing ecosystem of
[packages](https://www.guild.ai/packages/).

Refer to [https://www.guild.ai](https://www.guild.ai) for complete
coverage of Guild AI.

If you have questions or are facing problems, please open an issue at
[https://github.com/guildai/guildai/issues](https://github.com/guildai/guildai/issues).
