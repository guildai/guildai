# Model proxies

The module `guild.model_proxy` is used to resolve op specs under a
variety of circumstances:

- The special op spec "+" is used
- An op spec supported by a plugin via `resolve_model_op`

    >>> from guild import model_proxy

Plugins implement model proxy support for various op specs:

- Python scripts
- Keras scripts (specialized type of Python script)
- Executable scripts
- Optimizers

These tests illustate how various op specs are resolved.

We'll use the `model-proxies` sample project in these tests.

    >>> project = sample("projects", "model-proxies")

And a helper function to resolve op specs:

    >>> def resolve(opspec):
    ...     from guild import config
    ...     with config.SetCwd(project):
    ...         return model_proxy.resolve_model_op(opspec)

## Executable scripts

    >>> resolve("exec-script")
    (<guild.plugins.exec_script.ExecScriptModelProxy ...>, 'exec-script')

## Python scripts

    >>> resolve("python-script.py")
    (<guild.plugins.python_script.PythonScriptModelProxy ...>, 'python-script.py')

## Keras scripts

    >>> resolve("keras-script.py")
    (<guild.plugins.keras.KerasScriptModelProxy ..., 'keras-script.py')

## Default batch processor

    >>> resolve("+")
    (<guild.model_proxy.BatchModelProxy ...>, '+')

## Random optimizer

    >>> resolve("random")
    (<guild.plugins.skopt.RandomOptimizerModelProxy ...>, 'random')

    >>> resolve("skopt:random")
    (<guild.plugins.skopt.RandomOptimizerModelProxy ...>, 'random')

## Bayesian optimizer

    >>> resolve("gp")
    (<guild.plugins.skopt.GPOptimizerModelProxy ...>, 'gp')

    >>> resolve("skopt:gp")
    (<guild.plugins.skopt.GPOptimizerModelProxy ...>, 'gp')

## Not supported

    >>> resolve("never heard of")
    Traceback (most recent call last):
    NotSupported
