# Guild namespaces

Guild namespaces are manged with the `guild.namespace` module:

    >>> import guild.namespace

A namespace is a component of a Guild package reference. A namespace
is a package term (alpha-numeric string that may include dashes and
underscores) preceded by a '@' character.

Before using namespaces in Guild, we need to explicitly initialize
them.

    >>> guild.namespace.init_namespaces()

The following namespaces are supported:

    >>> sorted(guild.namespace.iter_namespaces())
    [('gpkg', <guild.namespace.gpkg object ...>),
     ('pypi', <guild.namespace.pypi object ...>)]

Namespaces implement functions related to Guild packages. These
include translating a Guild package name into a Python project and
providing install and search URLs for pip compatible indexes.

## pypi

Let's look at the `pypi` namespace:

    >>> pypi_ns = guild.namespace.for_name("pypi")

A Guild package `@pypy/keras` is translated to a Python project as
follows:

    >>> pypi_ns.python_project("keras")
    'keras'

Here we see that any package specified under the `pypi` namespace is
unmodified.

The `pypi` namespace provides the following index URLs:

    >>> pypi_ns.index_install_urls()
    ['https://https://pypi.python.org/simple']

    >>> pypi_ns.index_search_urls()
    ['https://pypi.python.org/pypi']

## gpkg

Let's now look at the `gpkg` namespace:

    >>> gpkg_ns = guild.namespace.for_name("gpkg")

A Guild package `@gpkg/mnist` is translated to a Python project as
follows:

    >>> gpkg_ns.python_project("mnist")
    'gpkg.mnist'

Here we see that any package specified under the `gpkg` namespace is
translated into a project with a `gpkg.` prefix. This is the standard
naming convention for all Guild packages.

The `gpkg` namespace provides the same URLs as the `pypi` namespace:

    >>> gpkg_ns.index_install_urls() == pypi_ns.index_install_urls()
    True

    >>> gpkg_ns.index_search_urls() == pypi_ns.index_search_urls()
    True
