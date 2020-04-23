# `tensorboard` package info

Projects from PyPI are under the `pypi` namespace.

We can use `guild packages info PKG` to show details about the
installed `pypi.tensorboard` package.

    >>> run("guild packages info tensorboard")  # doctest: -PY2
    name: tensorboard
    version: 2.2...
    summary: TensorBoard lets you watch Tensors Flow
    home-page: https://github.com/tensorflow/tensorboard
    author: Google Inc.
    author-email: ...
    license: Apache 2.0
    location: ...
    requires: ...
    required-by: guildai
    <exit 0>

    >>> run("guild packages info tensorboard")  # doctest: -PY3
    name: tensorboard
    version: 2.1...
    summary: TensorBoard lets you watch Tensors Flow
    home-page: https://github.com/tensorflow/tensorboard
    author: Google Inc.
    author-email: ...
    license: Apache 2.0
    location: ...
    requires: ...
    required-by: guildai
    <exit 0>
