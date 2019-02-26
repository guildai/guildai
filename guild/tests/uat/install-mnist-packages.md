# Install MNIST packages

In this test we'll install two `mnist` packages - one under the `gpkg`
namespace (Guild's default namespace) and another not under a
namespace (the originl `mnist` package in PyPI).

The package `gpkg.mnist` contains MNIST models:

    >>> quiet("guild install gpkg.mnist --pre --no-cache")

The package `mnist` contains tools for working with MNIST data. We
don't use this package, but it illustrates how the Guild packaging
namespace is used to differentiate between packages of the same name.

    >>> quiet("guild install mnist")
