# User acceptance tests

These are run in order as a part of Guild AI's user acceptance test.

This file is used to run the tests. Any modifications to this file
will modify the acceptance test.

These tests expect Guild to be installed.

- [guild-version](guild-version.md)

## Check environment

*Check the environment.*

- [guild-check](guild-check.md)
- [initial-packages](initial-packages.md)
- [tensorboard-package-info](tensorboard-package-info.md)

## Guild tests

*Run Guild tests.*

- [upgrade-pip](upgrade-pip.md)
- [install-test-deps](install-test-deps.md)
- [guild-tests](guild-tests.md)

## Empty environment

*Guild behavior without packages, models, or runs.*

Before we start using Guild to train models, we use it to example an
empty environment. This includes demonstrating all of its list
commands and helpfulness to the user for operations on missing models.

- [initial-models](initial-models.md)
- [initial-ops](initial-ops.md)
- [initial-runs](initial-runs.md)
- [train-missing-model](train-missing-model.md)
- [run-with-missing-default-model](run-with-missing-default-model.md)

## Local examples

*Test examples defined in Guild repo*

- [guild-example-hello](guild-example-hello.md)
- [guild-example-bash](guild-example-bash.md)

## Training Guild package models

*Installing and training a model from a Guild package.*

One of Guild's main features is the ability to install and train
models from packages. We start here with various packages that
exercise core Guild functionality.

Before training some of our models, we need to install TensorFlow as a
prereq.

- [install-tensorflow](install-tensorflow.md)

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
- [hiplot-after-logreg-train](hiplot-after-logreg-train.md)
- [view-after-logreg-train](view-after-logreg-train.md)

Finally we'll uninstall the `mnist` package and verify that its
associated models and operations removed.

- [uninstall-mnist-package](uninstall-mnist-package.md)
- [mnist-package-info-after-uninstall](mnist-package-info-after-uninstall.md)
- [packages-after-mnist-uninstall](packages-after-mnist-uninstall.md)

### `hello` package

The `hello` package is a distributed version of the `hello`
example.

- [install-hello-package](install-hello-package.md)

This package provide a single model with several operations that
exercise core Guild functionality. For simplicity all of the tests are
contained in a single file file.

- [run-hello-package-examples](run-hello-package-examples.md)

### `keras.mnist` package

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

*Run Guild examples.*

### Simple example

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
- [list-hello-examples](list-hello-examples.md)
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
- [train-keras-mlp-example-2](train-keras-mlp-example-2.md)

### Other examples

- [custom-scalars-example](custom-scalars-example.md)
- [flags-example](flags-example.md)

## Dependencies

- [required-operation](required-operation.md)
- [dependencies.md](dependencies.md)

## Staging and Queues

- [stage-and-run](stage-and-run.md)
- [stage-and-run-queue](stage-and-run-queue.md)
- [stage-and-modify-queue](stage-and-modify-queue.md)
- [stage-deps](stage-deps.md)
- [blocking-queues](blocking-queues.md)
- [concurrent-queues](concurrent-queues.md)
- [gpu-queues](gpu-queues.md)

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

## TensorFlow versions

Tests addressing various versions of TensorFlow, API changes, etc.

- [tensorflow1.md](tensorflow1.md)
- [tensorflow2.md](tensorflow2.md)

## PyTorch tests

- [install-pytorch.md](install-pytorch.md)

## Other tests

*Tests covering miscellaneous behavior.*

- [command-errors](command-errors.md)
- [alt-run-dir](alt-run-dir.md)
- [diff](diff.md)
- [guild-env](guild-env.md)
- [run-in-background](run-in-background.md)
- [run-stop-after](run-stop-after.md)
- [batch-preview](batch-preview.md)
- [project-sourcecode](project-sourcecode.md)
- [labels](labels.md)
- [tags](tags.md)
- [api-example](api-example.md)
- [flags-test](flags-test.md)
- [guild-open](guild-open.md)
- [export-import](export-import.md)
- [pip-freeze](pip-freeze.md)
- [no-run-output](no-run-output.md)
- [staged-dependency-error](staged-dependency-error.md)
- [link-vs-copy-dep](link-vs-copy-dep.md)
- [test-flags](test-flags.md)
- [tensorboard-export-scalars](tensorboard-export-scalars.md)
- [tensorboard-versions](tensorboard-versions.md)
- [guild-patch](guild-patch.md)
- [completion-command](completion-command.md)

## Error cases

*Guild behavior with various error cases.*

- [invalid-chdir](invalid-chdir.md)

## Remotes

- [remote-invalid-remote](remote-invalid-remote.md)
- [remote-check](remote-check.md)
- [remote-delete-runs](remote-delete-runs.md)
- [remote-run-hello-legacy](remote-run-hello-legacy.md)
- [remote-run-hello](remote-run-hello.md)
- [remote-run-hello-2](remote-run-hello-2.md)
- [remote-runs-after-hello](remote-runs-after-hello.md)
- [remote-ls-after-hello](remote-ls-after-hello.md)
- [remote-runs-info-after-hello](remote-runs-info-after-hello.md)
- [remote-cat-after-hello](remote-diff-after-hello.md)
- [remote-diff-after-hello](remote-diff-after-hello.md)
- [remote-watch-last-hello](remote-watch-last-hello.md)
- [remote-stop-last-hello](remote-stop-last-hello.md)
- [remote-label-hello](remote-label-hello.md)
- [remote-tag-hello](remote-tag-hello.md)
- [remote-comment-hello](remote-comment-hello.md)
- [remote-pull-hello](remote-pull-hello.md)
- [remote-push-hello](remote-push-hello.md)
- [remote-runs-info-after-push](remote-runs-info-after-push.md)
- [remote-sync](remote-sync.md)
- [remote-try-run-script](remote-try-run-script.md)
- [remote-ssh-stage-and-queue](remote-stage-and-start.md)
- [remote-ssh-stage-and-queue](remote-queue-and-stage.md)
- [remote-deps](remote-deps.md)
- [remote-s3](remote-s3.md)
