# Install test dependencies

Tests require additional packages that are not included in the Guild
distribution or requirements.txt. They are defined in
requirements-test.txt.

    >>> quiet("pip install -r $GUILD_PKGDIR/guild/tests/requirements.txt", timeout=180)

Run Guild check with verbose to show various module versions. We need
different tests for different versions of Python.

Python 3.6:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY36
    guild_version:             ...
    psutil_version:            5.8.0
    tensorboard_version:       2.4.1
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    dask_version:              2021...
    distutils_version:         ...
    numpy_version:             1.19.5
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.1
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.4.1
    yaml_version:              5.4.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.7:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY37
    guild_version:             ...
    psutil_version:            5.8.0
    tensorboard_version:       2.4.1
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    dask_version:              2021...
    distutils_version:         ...
    numpy_version:             1.20.2
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.1
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.4.1
    yaml_version:              5.4.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.8:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY38
    guild_version:             ...
    psutil_version:            5.8.0
    tensorboard_version:       2.4.1
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    dask_version:              2021...
    distutils_version:         ...
    numpy_version:             1.20.2
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.1
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.4.1
    yaml_version:              5.4.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.9:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY39
    guild_version:             ...
    psutil_version:            5.8.0
    tensorboard_version:       2.4.1
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    dask_version:              2021...
    distutils_version:         ...
    numpy_version:             1.20.2
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.1
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.4.1
    yaml_version:              5.4.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>
