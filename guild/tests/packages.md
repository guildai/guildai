# Guild packages

Guild packages are installable units that contain models, datasets, or
software libraries. They are standard Python packages that can be
installed and managed using `pip` commands.

`guild.package` provides tools for working with packages.

    >>> from guild import package

Package names include namespaces, either by explicitly including a
namespace, or implicitly by way of a default namespace.

Because we're working with namespaces, which are extensible by way of
distribution entry points, we need to limit our tests to built-in
namespaces:

    >>> from guild import namespace
    >>> namespace.limit_to_builtin()

## Splitting package names

The function `split_name` can be used to split a Guild package name
into a tuple of namespace and split name:

    >>> package.split_name("mnist")
    (<guild.namespace.Namespace 'gpkg'>, 'mnist')

Here we see that the Guild package `mnist` is implicitly a part of the
`gpkg` namespace. It it equivalent to `gpkg/mnist`:

    >>> package.split_name("gpkg/mnist")
    (<guild.namespace.Namespace 'gpkg'>, 'mnist')

The other namespace currently supported by Guild is `pypi`. This
namespace is used to explicitly reference a package installable from
PyPI.

    >>> package.split_name("pypi/mnist")
    (<guild.namespace.Namespace 'pypi'>, 'mnist')

If we try to split a name containing an unknown namespace, we get an
error:

    >>> package.split_name("other/mnist")
    Traceback (most recent call last):
    NamespaceError: other

## Applying namespaces to projects

A PyPI project may implicitly fall under a namespace. We can apply a
namespace to a project name using `apply_namespace`.

    >>> package.apply_namespace("mnist")
    'pypi/mnist'

    >>> package.apply_namespace("gpkg.mnist")
    'mnist'
