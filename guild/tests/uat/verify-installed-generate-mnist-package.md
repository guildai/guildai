---
doctest: -PY3 +PY36 +PY37  # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

# Verify installed generated `mnist` package

    >>> run("guild packages info gpkg.mnist")
    name: gpkg.mnist
    version: ...
    summary: CNN and multinomial logistic regression classifiers for MNIST digits (Guild AI)
    home-page: https://github.com/guildai/index/tree/master/gpkg/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../lib/python.../site-packages
    requires:...
    required-by:...
    <exit 0>

    >>> run("guild models mnist")
    gpkg.mnist/cnn      CNN classifier for MNIST
    gpkg.mnist/logreg   Multinomial logistic regression classifier for MNIST
    gpkg.mnist/samples  Sample MNIST images
    <exit 0>

    >>> run("guild operations mnist")
    gpkg.mnist/cnn:evaluate     Evaluate a trained CNN
    gpkg.mnist/cnn:train        Train the CNN
    gpkg.mnist/logreg:evaluate  Evaluate a trained logistic regression
    gpkg.mnist/logreg:train     Train the logistic regression
    gpkg.mnist/samples:prepare  Generate a set of sample MNIST images
    <exit 0>
