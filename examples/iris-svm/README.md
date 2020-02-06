# Guild Example: `iris-svm`

This example is an adaptation of the sciki-learn [SVM
Exercise](https://scikit-learn.org/stable/auto_examples/exercises/plot_iris_exercise.html).

- [guild.yml](guild.yml) - Project Guild file
- [plot_iris_exercise.py](plot_iris_exercise.py) - Tutorial exercise for using different SVM kernels

Operations:

- [`fit`](#fit) - Fit SVM model
- [`search`](#search) - Run a search for optimal hyperparameters

## `fit`

The `fit` operation runs the
[`plot_iris_exercise`](plot_iris_exercise.py) module, which is a
modified version of the code from [SVM
Exercise](https://scikit-learn.org/stable/auto_examples/exercises/plot_iris_exercise.html).

Modifications:

- Configure `matplotlib` to use the Agg backend. This allows the
  script to be automated.
- Use hyperparameter variables to let us experiment with different
  values.
- Run a single `fit` operation on the selected model type rather than
  on a hard-coded list of models. This lets us measure one model per
  script run.
- Save plots rather than show them in a GUI. This lets us automate
  runs and, importantly, save the plot artifacts so that we have a
  record corresponding to each run.

## `search`

To run the default operations:

    $ guild run fit

To search for optimal hyperparamters, run `search`:

    $ guild run search

To explore results visually, use the HParams tab of TensorBoard.

    $ guild tensorboard
