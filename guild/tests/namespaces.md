# Guild namespaces

A namespace is an optional leading component of a Guild package
reference that consists of a package term (i.e. terms that are
unmodified by `pkg_sources.safe_name`) that is separated from the rest
of the package reference with '/'. Namespaces are used to:

- Fully qualify package names so they unambiguously refer to a package
  distribution

- Provide information that can be used to install a package using pip

Examples of namespaces in package names:

    pypi.mnist
    gpkg.mnist
    ./mnist

Each of these fully qualified package names refers to a different
package. The first refers to the `mnist` project on PyPI. The second
refers to `gpkg.mnist` on PyPI. The third refers to a local guildfile
distribution in a directory named `mnist`.

Guild namespaces are manged with the `guild.namespace` module:

    >>> from guild import namespace

Namespaces can be registered by installing packages that provide entry
points for the "guild.namespaces" group. For these tests, we want to
ensure we are only working with built-ins:

    >>> namespace.limit_to_builtin()

We can use `iter_namespaces` to list the supported namespaces:

    >>> sorted(namespace.iter_namespaces())
    [('guildfile', <guild.namespace.Namespace 'guildfile'>),
     ('pypi', <guild.namespace.Namespace 'pypi'>)]

We can use `for_name` to lookup namespaces by name:

    >>> pypi = namespace.for_name("pypi")
    >>> gfns = namespace.for_name("guildfile")

We get NamespaceError if the namespace doesn't exist (note that the
'gpkg' namespace was removed for 0.5):

    >>> namespace.for_name("gpkg")
    Traceback (most recent call last):
    NamespaceError: gpkg

If a name isn't registered as a namespace, `for_name` raises an error:

    >>> namespace.for_name("other")
    Traceback (most recent call last):
    NamespaceError: other

## Package names and pip

Guild uses pip to install and manage packages. However, Guild does not
use PyPI project names in its package related operations. This is to
allow the Guild ecosystem to define its own packages without concern
for existing and future PyPI projects.

For example, the PyPI project `mnist` is Python software library for
working with the MNIST dataset. Guild's package `mnist` is model
package containing CNN and softmax classifiers and is stored in PyPI
under the `gpkg.mnist` project. Namespaces are used to qualify Guild
package references so they can be used with pip to install and manage
the appropriate PyPI packages.

Using the `mnist` package example, let's use namespaces to get the
information we need for working with pip packages:

    >>> pypi.pip_info("mnist")
    PipInfo(project_name='mnist',
            install_urls=['https://pypi.python.org/simple'])

    >>> pypi.pip_info("gpkg.mnist")
    PipInfo(project_name='gpkg.mnist',
            install_urls=['https://pypi.python.org/simple'])

Some namespaces may not support `pip_info`:

    >>> gfns.pip_info(".guildfile.ABC")
    Traceback (most recent call last):
    TypeError: guildfiles cannot be installed using pip

Here we see that, under the `pypi` namespace, `mnist` refers to the
same project name whereas, under `gpkg`, it refers to `gpkg.mnist`.

## Pip project name membership

Namespaces can be used to test if a pip project name is a member using
`project_name_membership`. Namespace membership falls into one of three
values:

- "yes", the project name is a member of the namespace
- "no", the project name is not a member
- "maybe", the project name might be a member

Let's test the `mnist` package:

    >>> pypi.project_name_membership("mnist")
    'maybe'

    >>> gfns.project_name_membership("mnist")
    'no'

Here we see that the package `mnist` might be a member of the `pypi`
namespace. The package is not however a member of the `gpkg`
namespace.

Let's test a guildfile project name:

    >>> pypi.project_name_membership(".guildfile.ABC")
    'maybe'

    >>> gfns.project_name_membership(".guildfile.ABC")
    'yes'

Here we see that the project name `gpkg.mnist` might be a member of
the `pypi` namespace and would be named `pypi.gpig.mnist` if it
is. However, `gpkg` is laying full claim to the project and names it
`mnist`.

## Package names

Namespaces can be used to generate Guild package names given a Python
project name.

The `pypi` namespace uses the package name without modification:

    >>> pypi.package_name("mnist")
    'mnist'

    >>> pypi.package_name("gpkg.mnist")
    'gpkg.mnist'

The guildfile namespace decodes the project name to a Guild file
path:

    >>> gfns.package_name(".guildfile.2F666F6F")
    '/foo'

If a project name is not in a namespace, the namespace raises TypeError:

    >>> gfns.package_name("mnist")
    Traceback (most recent call last):
    TypeError: mnist is not a member of guildfile namespace

## Guildfile namespace

Guild provides a special namespace for guildfile packages. A guildfile
package is a local directory containing a guildfile (i.e. a file named
`guild.yml`). If a guildfile package is on the Python path, Guild will
see any models defined in it.

    >>> guildfile = namespace.for_name("guildfile")

Guildfile packages cannot be installed using pip:

    >>> guildfile.pip_info("mnist")
    Traceback (most recent call last):
    TypeError: guildfiles cannot be installed using pip

However, they can be used to test project name membership and
translate a guildfile project name into a package name.

Modefile project names are in the format:

    '.guildfile.' + ESCAPED_PROJECT_NAME

Project names are escaped because they may contain 'unsafe' character
that are disallowed in standard project names.

Any project name that doesn't start with '.guildfile.' is not
considered a member:

    >>> guildfile.project_name_membership("mnist")
    'no'

    >>> guildfile.project_name_membership("gpkg.mnist")
    'no'

Let's create a modefile project name. We'll need a helper:

    >>> from guild.model import escape_project_name

And our project name:

    >>> guildfile_project = ".guildfile." + escape_project_name("foo/bar")

Let's test it!

    >>> guildfile.project_name_membership(guildfile_project)
    'yes'

    >>> guildfile.package_name(guildfile_project)
    'foo/bar'

Here we see that our guildfile project name is the `foo/bar` package.

For more information about guildfile package names, see the [packages
test](packages.md).

## Applying namespaces

The function `apply_namespace` can be used to apply a namespace to a
project name and return a package name:

    >>> namespace.apply_namespace("mnist")
    'mnist'

    >>> namespace.apply_namespace("gpkg.mnist")
    'gpkg.mnist'

    >>> namespace.apply_namespace(".guildfile." + escape_project_name("/bar"))
    '/bar'

## Splitting package names

The function `split_name` can be used to split a Guild package name
into a tuple of namespace and split name:

    >>> namespace.split_name("mnist")
    (<guild.namespace.Namespace 'pypi'>, 'mnist')

    >>> namespace.split_name("gpkg.mnist")
    (<guild.namespace.Namespace 'pypi'>, 'gpkg.mnist')
