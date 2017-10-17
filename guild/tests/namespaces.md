# Guild namespaces

Guild namespaces are manged with the `guild.namespace` module:

    >>> import guild.namespace

A namespace is a component of a Guild package reference. A namespace
is a package term (alpha-numeric string that may include dashes and
underscores) preceded by a '@' character.

Namespaces can be registered by installing packages that provide entry
points for the "guild.namespaces" group. For these tests, we want to
ensure we are only working with built-ins:

    >>> guild.namespace.limit_to_builtin()

Let's use `iter_namespaces` to list the supported namespaces:

    >>> sorted(guild.namespace.iter_namespaces())
    [('gpkg', <guild.namespace.gpkg object ...>),
     ('pypi', <guild.namespace.pypi object ...>)]

Namespaces implement functions that are used in conjunction with
package operations, including install and searching.

## pypi

Packages that start with `@pypi/` fall under the `pypi` namespace.

    >>> pypi_ns = guild.namespace.for_name("pypi")
    >>> pypi_ns.name
    'pypi'

To install a Guild package `@pypi/mnist`, we can use `pip` with the
following information:

    >>> pypi_ns.pip_install_info("mnist")
    ('mnist', ['https://pypi.python.org/simple'])

Namespaces can also be used to test a project name for namespace
membership. Membership can have one of three values:

- guild.namespace.Membersip.yes
- guild.namespace.Membership.no
- guild.namespace.Membership.maybe

The test also returns the package name

The `pypi` namespace test always returns maybe:

    >>> pypi_ns.is_member("mnist")
    ('maybe', 'mnist')

    >>> pypi_ns.is_member("guild.mnist")
    ('maybe', 'guild.mnist')

## gpkg

Packages that start with `@gpkg/` fall under the `gpkg` namespace.

    >>> gpkg_ns = guild.namespace.for_name("gpkg")
    >>> gpkg_ns.name
    'gpkg'

To install a Guild package `@gpkg/mnist`, we can use `pip` with the
following information:

    >>> gpkg_ns.pip_install_info("mnist")
    ('gpkg.mnist', ['https://pypi.python.org/simple'])

Here we see that any package specified under the `gpkg` namespace is
translated into a value with a `gpkg.` prefix. This is the standard
naming convention for all Guild packages.

We also see that Guild packages are installed from PyPI.

The `gpkg` namespace will consider a project to be a member if it
starts with `gpkg.`:

    >>> gpkg_ns.is_member("gpkg.mnist")
    ('yes', 'mnist')

But not otherwise:

    >>> gpkg_ns.is_member("mnist")
    ('no', None)

## Other namespaces

`for_name` raises `LookupError` if a namespace doesn't exist:

    >>> guild.namespace.for_name("other")
    Traceback (most recent call last):
    LookupError: other
