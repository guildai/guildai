# User acceptance tests

These are run in order as a part of Guild AI's user acceptance test.

This file is used to run the tests. Any modifications to this file
will modify the acceptance test.

These tests expect Guild to be installed.

- [guild-version](guild-version.md)

## Initialize env

*Initializing Guild env.*

We can initialize the Guild environment, including installing
TensorFlow using the `init` command.

- [check-before-init](check-before-init.md)
- [tensorflow-commands-before-init](tensorflow-commands-before-init.md)
- [init-env](init-env.md)
- [check-after-init](check-after-init.md)
- [guild-tests](guild-tests.md)

## Command errors

*Run commands with missing arguments and other errors.*

- [command-errors](command-errors.md)

## Sample project

*Initializing and training a sample project*

- [init-sample-project](init-sample-project.md)
- [reinit-sample-project](reinit-sample-project.md)
- [sample-project-info](sample-project-info.md)
- [train-sample-project](train-sample-project.md)
- [sample-project-run](sample-project-run.md)
- [delete-sample-run](delete-sample-run.md)

## Empty environment

*Guild behavior without packages, models, or runs.*

Before we start using Guild to train models, we use it to example an
empty environment. This includes demonstrating all of its list
commands and helpfulness to the user for operations on missing models.

- [initial-packages](initial-packages.md)
- [tensorboard-package-info](tensorboard-package-info.md)
- [initial-models](initial-models.md)
- [initial-ops](initial-ops.md)
- [initial-resources](initial-resources.md)
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
`cnn` and `softmax` respectively.

First we install the package.

- [install-mnist-packages](install-mnist-packages.md)

Then we confirm we have the expected models, operations and resources.

- [mnist-package-info](mnist-package-info.md)
- [packages-after-mnist-install](packages-after-mnist-install.md)
- [models-after-mnist-install](models-after-mnist-install.md)
- [ops-after-mnist-install](ops-after-mnist-install.md)
- [resources-after-mnist-install](resources-after-mnist-install.md)

Next we train the `softmax` model and view the results.

- [tmp-mnist-data-before-softmax-train](tmp-mnist-data-before-softmax-train.md)
- [train-mnist-softmax-preview](train-mnist-softmax-preview.md)
- [train-mnist-softmax](train-mnist-softmax.md)
- [runs-after-mnist-softmax-train](runs-after-mnist-softmax-train.md)
- [run-info-after-mnist-softmax-train](run-info-after-mnist-softmax-train.md)
- [tmp-mnist-data-after-softmax-train](tmp-mnist-data-after-softmax-train.md)
- [compare-after-softmax-train](compare-after-softmax-train.md)
- [view-after-softmax-train](view-after-softmax-train.md)

Next we prepare sample images and run some predictions.

- [serve-after-softmax-train](serve-after-softmax-train.md)
- [prepare-mnist-samples](prepare-mnist-samples.md)
- [predict-mnist-samples](predict-mnist-samples.md)

Before we uninstall the package, we'll take advantage of the fact we
have multiple models containing the term "mnist" and test an error
condition.

- [train-multiple-matches](train-multiple-matches.md)

Finally we'll uninstall the `mnist` package and verify that its
associated operations, models, and resources are removed.

- [uninstall-mnist-package](uninstall-mnist-package.md)
- [mnist-package-info-after-uninstall](mnist-package-info-after-uninstall.md)
- [packages-after-mnist-uninstall](packages-after-mnist-uninstall.md)
- [models-after-mnist-uninstall](models-after-mnist-install.md)
- [ops-after-mnist-install](ops-after-mnist-install.md)
- [resources-after-mnist-uninstall](resources-after-mnist-uninstall.md)

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

First we'll install the package and confirm the availbility of models,
operations and resources.

- [install-keras-mnist-package](install-keras-mnist-package.md)
- [packages-after-keras-mnist-install](packages-after-keras-mnist-install.md)
- [models-after-keras-mnist-install](models-after-keras-mnist-install.md)
- [operations-after-keras-mnist-install](operations-after-keras-mnist-install.md)
- [resources-after-keras-mnist-install](resources-after-keras-mnist-install.md)

Next we'll train the `mnist-mlp` model.

- [train-keras-mnist-mlp](train-keras-mnist-mlp.md)

## Training Guild example models

*Installing and training Guild examples.*

Guild examples are similar to package source, but they are indepedent
and may have different features and behavior. We test them here as a
matter of coverage and to take advantage of any differences.

- [install-examples](install-examples.md)

### `mnist` example

The `mnist` example is similar to the package of the same name. It
maintains its lineage from privious Guild releases by providing
`expert` and `intro` models, which correspond to the TensorFlow
tutorial examples.

We start by listing the example models, operations and resources.

- [mnist-example-models](mnist-example-models.md)
- [mnist-example-ops](mnist-example-ops.md)
- [mnist-example-resources](mnist-example-resources.md)

Next we train `intro`.

- [mnist-example-initial-runs](mnist-example-initial-runs.md)
- [train-mnist-intro-example](train-mnist-intro-example.md)
- [mnist-example-runs-after-intro-train](mnist-example-runs-after-intro-train.md)

Once we have a trained model we can run the `evaluate` operation on
it.

- [evaluate-mnist-intro-example](evaluate-mnist-intro-example.md)
- [mnist-example-runs-after-intro-evaluate](mnist-example-runs-after-intro-evaluate.md)

As a final check, we want to ensure that the example operations used
the data provided by the model file resource.

- [tmp-mnist-data-after-mnist-example](tmp-mnist-data-after-mnist-example.md)


### `hello` example

The `hello` example is a non ML model that simply prints messages to
the console. While trivial in this respect, its various operation
demonstrate important Guild features.

For simplicity we maintain a single test file.

- [run-hello-examples](run-hello-examples.md)

### `keras` example

The `keras` example demonstrates how plugins can enumerate models in a
directory and provide operations for compatible models.

For our tests of the example model, we'll first uninstall some
packages that were installed in pervious tests.

- [uninstall-keras-packages](uninstall-keras-packages.md)

And test the `keras` example.

- [keras-example-models](keras-example-models.md)
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

## Packages

### `slim.resnet`

- [slim-resnet-install](slim-resnet-install.md)
- [slim-resnet-ops](slim-resnet-ops.md)
- [slim-resnet-train-without-dataset](slim-resnet-train-without-dataset.md)
- [slim-resnet-prepare-flowers](slim-resnet-prepare-flowers.md)
- [slim-resnet-train-ambiguous](slim-resnet-train-ambiguous.md)
