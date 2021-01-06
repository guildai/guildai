# Install test dependencies

Tests require additional packages that are not included in the Guild
distribution or requirements.txt. They are defined in
requirements-test.txt.

    >>> quiet("pip install $TEST_DEPS_OPTS -r  $GUILD_PKGDIR/guild/tests/requirements.txt")

Run Guild check with verbose to show various module versions. We need
different tests for different versions of Python.

Python 2.7:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY27
    guild_version:             ...
    psutil_version:            5.6.3
    tensorboard_version:       2.1.0
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    distutils_version:         ...
    numpy_version:             1.16.6
    pandas_version:            0.24.2
    pip_version:               18.0
    sklearn_version:           0.20.4
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             1.15.0
    yaml_version:              5.3.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.5:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY35
    guild_version:             ...
    psutil_version:            5.6.3
    tensorboard_version:       2.4.0
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             7.1.2
    distutils_version:         ...
    numpy_version:             1.18.5
    pandas_version:            0.25.3
    pip_version:               18.0
    sklearn_version:           0.22.2.post1
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             1.15.0
    yaml_version:              5.3.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.6:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY36
    guild_version:             ...
    psutil_version:            5.6.3
    tensorboard_version:       2.4.0
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             8.0.0a1
    distutils_version:         ...
    numpy_version:             1.19.5
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.0
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.3.0
    yaml_version:              5.3.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.7:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY37
    guild_version:             ...
    psutil_version:            5.6.3
    tensorboard_version:       2.4.0
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             8.0.0a1
    distutils_version:         ...
    numpy_version:             1.19.5
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.0
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.3.0
    yaml_version:              5.3.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>

Python 3.8:

    >>> run("guild check --verbose --offline")  # doctest: -PY2 -PY3 +PY38
    guild_version:             ...
    psutil_version:            5.6.3
    tensorboard_version:       2.4.0
    cuda_version:              ...
    nvidia_smi_version:        ...
    click_version:             8.0.0a1
    distutils_version:         ...
    numpy_version:             1.19.5
    pandas_version:            1.1.5
    pip_version:               18.0
    sklearn_version:           0.24.0
    skopt_version:             0.8.1
    setuptools_version:        ...
    twine_version:             3.3.0
    yaml_version:              5.3.1
    werkzeug_version:          1.0.1
    latest_guild_version:      ...
    <exit 0>
