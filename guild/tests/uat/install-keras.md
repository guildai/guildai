---
doctest: -PY3 +PY36 +PY37 +PY38 # 2022-04-11 on python 3.9+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.9+
---


# Install keras

We can install the `Keras` package from PyPI using this command:

    >>> quiet("guild install 'keras<2.4'")

And the installed version:

    >>> run("guild packages list -a keras")
    Keras                2.3...  Deep Learning for humans
    Keras-Applications   1.0...  Reference implementations of popular deep learning models
    Keras-Preprocessing  1.1...  Easy data preprocessing and data augmentation ...
    <exit 0>

We need to make sure h5py is installed for Keras checkpoints to be
created.

    >>> quiet("pip install 'h5py<3' --upgrade --force")
