# Guild version

This test assumes we're running under the source tree, which indicates
"dev" mode. The version reflects this.

    >>> run("guild --version")
    guild 0.9.1...
    <exit 0>

Use `check` to verfiy that we are running the expected version:

    >>> run("guild check -n --version '>0.9.0'")
    <exit 0>

Specify an invalid version.

    >>> run("guild check -n --version 0.1.0")
    guild: version mismatch: current version '...' does not match '0.1.0'
    <exit 1>
