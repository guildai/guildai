# Upgrade pip

Make sure we're running the latest pip.

    >>> quiet("pip install --upgrade pip")

Confirm we're on the expected version.

    >>> run("pip --version")
    pip 21.0 from .../site-packages/pip (python ...)
    <exit 0>
