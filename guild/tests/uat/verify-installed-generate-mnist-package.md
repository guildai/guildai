# Verify installed generated `mnist` package

    >>> run("guild packages info mnist")
    name: mnist
    version: ...
    summary: CNN and softmax regression classifiers for MNIST digits
    home-page: https://github.com/guildai/index/tree/master/mnist
    author: Guild AI
    author-email: packages@guild.ai
    license: Apache 2.0
    location: /.../guild-uat/lib/python.../site-packages
    requires: gpkg.mnist-dataset
    <exit 0>

    >>> run("guild models mnist")
    mnist/mnist-cnn      CNN classifier for MNIST
    mnist/mnist-softmax  Softmax regression classifier for MNIST
    <exit 0>

    >>> run("guild operations mnist")
    mnist/mnist-cnn:train      Train the CNN
    mnist/mnist-softmax:train  Train the softmax regression
    <exit 0>

    >>> run("guild resources mnist")
    mnist-dataset/idx  Yann Lecun's MNIST dataset in compressed IDX format
    <exit 0>
