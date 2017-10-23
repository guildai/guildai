# User acceptance tests

These are run in order as a part of Guild AI's user acceptance test.

This file is used to run the tests. Any modifications to this file
will modify the acceptance test.

## Partial Guild install

*Guild behavior in a partially configured environment.*

- [fresh-install](fresh-install.md)
- [install-required-pip-packages](install-required-pip-packages.md)
- [check-without-tensorflow](check-without-tensorflow.md)

## Working Guild install

*Complete Guild configuration and initial checks.*

- [install-tensorflow](install-tensorflow.md)
- [check-with-tensorflow](check-with-tensorflow.md)
- [guild-tests](guild-tests.md)

## Empty environment

*Guild behavior without packages, models, or runs.*

- [initial-packages](initial-packages.md)
- [initial-models](initial-models.md)
- [initial-ops](initial-ops.md)
- [initial-runs](initial-runs.md)
- [train-missing-model](train-missing-model.md)
- [run-with-missing-default-model](run-with-missing-default-model.md)

## Training a Guild package

*Installing and training a model from a Guild package.*

- [install-mnist-packages](install-mnist-packages.md)
- [packages-after-mnist-install](packages-after-mnist-install.md)
- [models-after-mnist-install](models-after-mnist-install.md)
- [ops-after-mnist-install](ops-after-mnist-install.md)
- [train-multiple-matches](train-multiple-matches.md)
- [train-mnist-softmax](train-mnist-softmax.md)
- [runs-after-mnist-softmax-train](runs-after-mnist-softmax-train.md)

## Training a Guild example

*Installing and training a Guild example.*

- [install-examples](install-examples.md)
- [mnist-example-models](mnist-example-models.md)
- [mnist-example-ops](mnist-example-ops.md)
- [mnist-example-initial-runs](mnist-example-initial-runs.md)
- [train-mnist-intro-example](train-mnist-intro-example.md)
- [mnist-example-runs-after-intro-train](mnist-example-runs-after-intro-train.md)

## Packaging

*Creating and installing packages.*

TODO: use a different package when one is available (e.g. keras, etc.)

- [install-index-source](install-index-source.md)
- [create-mnist-package](create-mnist-package.md)
- [uninstall-mnist-package](uninstall-mnist-package.md)
- [install-generated-mnist-package](install-generated-mnist-package.md)

## Error cases

*Guild behavior with various error cases.*

- [invalid-chdir](invalid-chdir.md)
