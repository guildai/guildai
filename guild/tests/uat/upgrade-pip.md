# Upgrade pip

Make sure we're running the latest pip.

    >>> quiet("pip install --upgrade pip")

Confirm we're on the expected version.

    >>> run("pip --version")  # doctest: -PY2 -PY35
    pip 21.0.1 from .../site-packages/pip (python ...)
    <exit 0>

    >>> run("pip --version")  # doctest: -PY3 +PY35
    pip 20.3.4 from .../site-packages/pip (python ...)
    <exit 0>
