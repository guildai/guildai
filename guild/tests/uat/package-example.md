# Package Example

    >>> cd(example("packages/a"))

    >>> quiet("guild package")
    >>> quiet("guild install dist/*")

    >>> cd(example("packages/b"))

    >>> quiet("guild package")
    >>> quiet("guild install dist/*")

    >>> run("guild packages")
    gpkg.a      0.0.0       Sample package
    gpkg.b      0.0.0       Sample package
    ...
    <exit 0>

    >>> run("guild ops")
    b:train
    <exit 0>

    >>> run("guild ops -i")
    gpkg.a/a:train
    gpkg.b/b:train
    ...
    b:train
    <exit 0>

    >>> quiet("guild runs rm -y")

Make sure we're in `b` dir (don't rely on state above):

    >>> cd(example("packages/b"))

    >>> run("guild run train -y")
    b
    <exit 0>

    >>> run("guild run b:train -y")
    b
    <exit 0>

This is the wrong spelling of the packaged operation:

    >>> run("guild run gpkg.b:train -y")
    guild: cannot find operation gpkg.b:train
    Try 'guild operations' for a list of available operations.
    <exit 1>

This is the correct spelling:

    >>> run("guild run gpkg.b/b:train -y")
    b
    <exit 0>

    >>> run("guild run a:train -y")
    a
    <exit 0>

    >>> run("guild run gpkg.a/a:train -y")
    a
    <exit 0>

    >>> run("guild runs")
    [1:...]  gpkg.a/a:train  ...  completed
    [2:...]  gpkg.a/a:train  ...  completed
    [3:...]  gpkg.b/b:train  ...  completed
    [4:...]  b:train         ...  completed
    [5:...]  b:train         ...  completed
    <exit 0>
