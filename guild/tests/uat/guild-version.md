# Guild version

This test assumes we're running under the source tree, which indicates
"dev" mode. The version reflects this.

    >>> run("guild --version")
    guild 0.7...
    <exit 0>

Use `check` to verfiy that we are running the expected version:

    >>> run("guild check -n --version '>=0.7,<0.8'")
    <exit 0>

And an incorrect version:

    >>> run("guild check -n --version 0.1.0")
    guild: version mismatch: current version '0.7...' does not match '0.1.0'
    <exit 1>
