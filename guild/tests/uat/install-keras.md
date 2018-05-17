# Install keras

We can install the `Keras` package from PyPI using this command:

    >>> quiet("guild install pypi.keras")

And the installed version:

    >>> run("guild packages list -a keras")
    pypi.Keras  2.1...  Deep Learning for humans
    <exit 0>

We need to make sure h5py is installed for Keras checkpoints to be
created.

    >>> quiet("pip install h5py --upgrade --force")
