# `gpkg.mnist` package info

Use `guild packages info PKG` to show information about a package:

    >>> run("guild packages info gpkg.mnist") # doctest: +REPORT_UDIFF
    name: gpkg.mnist
    version: 0.6.0...
    summary: CNN and multinomial logistic regression classifiers for MNIST digits (Guild AI)
    home-page: https://github.com/guildai/index/tree/master/gpkg/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../lib/python.../site-packages
    requires: []
    required-by: []
    <exit 0>

We can use the `--verbose` and `--files` flags to get more
information.

    >>> run("guild packages info gpkg.mnist --verbose --files") # doctest: +REPORT_UDIFF
    name: gpkg.mnist
    version: 0.6.0...
    summary: CNN and multinomial logistic regression classifiers for MNIST digits (Guild AI)
    home-page: https://github.com/guildai/index/tree/master/gpkg/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../lib/python.../site-packages
    requires: []
    required-by: []
    metadata-version: 2.1
    installer: pip
    classifiers:
    entry-points:
      [guild.models]
      _check = guild.model:PackageModel
      cnn = guild.model:PackageModel
      logreg = guild.model:PackageModel
      samples = guild.model:PackageModel
      [guild.resources]
      cnn:mnist-dataset = guild.model:PackageModelResource
      cnn:trained-model = guild.model:PackageModelResource
      logreg:mnist-dataset = guild.model:PackageModelResource
      logreg:trained-model = guild.model:PackageModelResource
      samples:mnist-dataset = guild.model:PackageModelResource
    files:
      ...
    <exit 0>
