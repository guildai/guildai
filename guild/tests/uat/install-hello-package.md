# Install `gpkg.hello` package

The `gpkg.hello` package is used to test some basic functionality without
actually training anything.

    >>> quiet("guild install gpkg.hello --pre --no-cache")

Once installed we have a `hello` model:

    >>> run("guild models hello", ignore="Refreshing")
    gpkg.hello/hello          A "hello world" sample model
    <exit 0>

and related operations:

    >>> run("guild operations hello")
    gpkg.hello/hello:default           Print a default message
    gpkg.hello/hello:from-file         Print a message from a file
    gpkg.hello/hello:from-file-output  Print output from last file-output operation
    gpkg.hello/hello:from-flag         Print a message
    <exit 0>
