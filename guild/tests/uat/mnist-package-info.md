# `mnist` package info

Use `guild packages info PKG` to show information about a package:

    >>> run("guild packages info mnist") # doctest: +REPORT_UDIFF
    name: mnist
    version: 0.1.2.dev1
    summary: CNN and softmax regression classifiers for MNIST digits
    home-page: https://github.com/guildai/index/tree/master/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../guild-uat/lib/python.../site-packages
    requires: gpkg.mnist-dataset
    <exit 0>

We can use the `--verbose` and `--files` flags to get more
information.

    >>> run("guild packages info mnist --verbose --files") # doctest: +REPORT_UDIFF
    name: mnist
    version: 0.1.2.dev1
    summary: CNN and softmax regression classifiers for MNIST digits
    home-page: https://github.com/guildai/index/tree/master/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../guild-uat/lib/python.../site-packages
    requires: gpkg.mnist-dataset
    metadata-version: 2.0
    installer: pip
    classifiers:
    entry-points:
      [guild.models]
      mnist-cnn = guild.model:PackageModel
      mnist-softmax = guild.model:PackageModel
    files:
      ...
    <exit 0>
