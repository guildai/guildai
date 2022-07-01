# TensorFlow commands before init

This test runs various commands that require the tensorflow or
tensorboard packages.

We're assuming that neither are installed at this point:

    >>> run("python -c 'import tensorflow'")
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ...: No module named ...tensorflow...
    <exit 1>

    >>> run("python -c 'import tensorboard'")
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ...: No module named ...tensorboard...
    <exit 1>

The `tensorboard` command won't run unless TensorFlow is installed:

    >>> run("guild tensorboard", timeout=1)
    TensorBoard cannot not be started because TensorFlow is not installed.
    Refer to https://www.tensorflow.org/install/ for help installing TensorFlow
    on your system.
    <exit 1>

The `tensorflow inspect` command uses TensorFlow:

    >>> run("guild tensorflow inspect foo")
    TensorFlow is not installed.
    Refer to https://www.tensorflow.org/install/ for help installing TensorFlow
    on your system.
    <exit 1>
