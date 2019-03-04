# User acceptance tests

These are run in order as a part of Guild AI's user acceptance test.

This file is used to run the tests. Any modifications to this file
will modify the acceptance test.

These tests expect Guild to be installed.

- [guild-version](guild-version.md)

## Env check and unit tests

*Check the environment and run unit tests.*

- [guild-check](guild-check.md)
- [guild-tests](guild-tests.md)

## Command errors

*Run commands with missing arguments and other errors.*

- [command-errors](command-errors.md)

## Empty environment

*Guild behavior without packages, models, or runs.*

Before we start using Guild to train models, we use it to example an
empty environment. This includes demonstrating all of its list
commands and helpfulness to the user for operations on missing models.

- [initial-packages](initial-packages.md)
- [tensorboard-package-info](tensorboard-package-info.md)
- [initial-models](initial-models.md)
- [initial-ops](initial-ops.md)
- [initial-runs](initial-runs.md)
- [train-missing-model](train-missing-model.md)
- [run-with-missing-default-model](run-with-missing-default-model.md)

## Training Guild package models

*Installing and training a model from a Guild package.*

One of Guild's main features is the ability to install and train
models from packages. We start here with various packages that
exercise core Guild functionality.

### `mnist` package

The `mnist` package contains two models that roughly correspond to the
TensorFlow *expert* and *intro* tutorial examples. These are named
`cnn` and `logreg` respectively.

First we install the package.

- [install-mnist-packages](install-mnist-packages.md)

Then we confirm we have the expected models and operations.

- [mnist-package-info](mnist-package-info.md)
- [packages-after-mnist-install](packages-after-mnist-install.md)
- [models-after-mnist-install](models-after-mnist-install.md)
- [ops-after-mnist-install](ops-after-mnist-install.md)

Next we train the `logreg` model and view the results.

- [tmp-mnist-data-before-logreg-train](tmp-mnist-data-before-logreg-train.md)
- [train-mnist-logreg-preview](train-mnist-logreg-preview.md)
- [train-mnist-logreg](train-mnist-logreg.md)
- [runs-after-mnist-logreg-train](runs-after-mnist-logreg-train.md)
- [run-info-after-mnist-logreg-train](run-info-after-mnist-logreg-train.md)
- [tmp-mnist-data-after-logreg-train](tmp-mnist-data-after-logreg-train.md)
- [compare-after-logreg-train](compare-after-logreg-train.md)
- [view-after-logreg-train](view-after-logreg-train.md)

Finally we'll uninstall the `mnist` package and verify that its
associated models and operations removed.

- [uninstall-mnist-package](uninstall-mnist-package.md)
- [mnist-package-info-after-uninstall](mnist-package-info-after-uninstall.md)
- [packages-after-mnist-uninstall](packages-after-mnist-uninstall.md)

### `hello`

The `hello` package is a distributed version of the `hello`
example.

- [install-hello-package](install-hello-package.md)

This package provide a single model with several operations that
exercise core Guild functionality. For simplicity all of the tests are
contained in a single file file.

- [run-hello-package-examples](run-hello-package-examples.md)

### `keras.mnist`

Guild provides Keras packages under the `keras` package
namespace. These tests demonstrate installing and training the
`keras-mlp` model provided in the `keras.mnist` package.

First we'll install the package and confirm the availbility of models
and operations.

- [install-keras-mnist-package](install-keras-mnist-package.md)
- [packages-after-keras-mnist-install](packages-after-keras-mnist-install.md)
- [models-after-keras-mnist-install](models-after-keras-mnist-install.md)
- [operations-after-keras-mnist-install](operations-after-keras-mnist-install.md)

Next we'll train the `mnist-mlp` model.

- [train-keras-mnist-mlp](train-keras-mnist-mlp.md)

## Training Guild example models

*Installing and training Guild examples.*

Guild examples are similar to package source, but they are indepedent
and may have different features and behavior. We test them here as a
matter of coverage and to take advantage of any differences.

- [install-examples](install-examples.md)

## Simple example

- [simple-example](simple-example.md)

### `mnist` example

The `mnist` example is similar to the package of the same name. It
maintains its lineage from privious Guild releases by providing
`expert` and `intro` models, which correspond to the TensorFlow
tutorial examples.

We start by listing the example models and operations.

- [mnist-example-models](mnist-example-models.md)
- [mnist-example-ops](mnist-example-ops.md)

Next we train `intro`.

- [train-mnist-intro-example](train-mnist-intro-example.md)
- [mnist-example-runs-after-intro-train](mnist-example-runs-after-intro-train.md)

Once we have a trained model we can run the `evaluate` operation on
it.

- [evaluate-mnist-intro-example](evaluate-mnist-intro-example.md)
- [mnist-example-runs-after-intro-evaluate](mnist-example-runs-after-intro-evaluate.md)

As a final check, we want to ensure that the example operations used
the data provided by the model file resource.

- [tmp-mnist-data-after-mnist-example](tmp-mnist-data-after-mnist-example.md)

The mnist example defines two models containing 'mnist', which lets us
test Guild's handling of an ambiguous model spec.

- [train-multiple-matches](train-multiple-matches.md)

### `hello` example

The `hello` example is a non ML model that simply prints messages to
the console. While trivial in this respect, its various operation
demonstrate important Guild features.

For simplicity we maintain a single test file.

- [run-hello-examples](run-hello-examples.md)
- [diff-hello-examples](diff-hello-examples.md)

### `keras` example

The `keras` example demonstrates how plugins can enumerate models in a
directory and provide operations for compatible models.

For our tests of the example model, we'll first uninstall some
packages that were installed in pervious tests.

- [uninstall-keras-packages](uninstall-keras-packages.md)

And test the `keras` example.

- [train-keras-example-with-missing-dep](train-keras-example-with-missing-dep.md)
- [install-keras](install-keras.md)
- [train-keras-mlp-example](train-keras-mlp-example.md)

## Packaging

*Creating and installing packages.*

Guild packages are generated from source directories that contain
guildfiles with a package definition. They may contain models and
their required scripts as well as package resoures.

For our tests, we'll build and install packages using sources from the
[`guild-index` GitHub repository](https://github.com/guildai/index).

- [install-package-source](install-package-source.md)

Here we build and install the `mnist` package, which is otherwise
identical to the distributed package we tested earlier.

- [create-mnist-package](create-mnist-package.md)
- [install-generated-mnist-package](install-generated-mnist-package.md)
- [verify-installed-generate-mnist-package](verify-installed-generate-mnist-package.md)

## Other tests

*Tests covering miscellaneous behavior.*

[alt-run-dir](alt-run-dir.md)

## Error cases

*Guild behavior with various error cases.*

- [invalid-chdir](invalid-chdir.md)

## Remotes

- [remote-invalid-remote](remote-invalid-remote.md)
- [remote-ssh-check](remote-ssh-check.md)
- [remote-ssh-delete-runs](remote-ssh-delete-runs.md)
- [remote-ssh-run-hello](remote-ssh-run-hello.md)
- [remote-ssh-runs-after-hello](remote-ssh-runs-after-hello.md)
- [remote-ssh-watch-last-hello](remote-ssh-watch-last-hello.md)
- [remote-ssh-stop-last-hello](remote-ssh-stop-last-hello.md)
- [remote-ssh-label-hello](remote-ssh-label-hello.md)
- [remote-ssh-pull-hello](remote-ssh-pull-hello.md)
- [remote-ssh-push-hello](remote-ssh-push-hello.md)
