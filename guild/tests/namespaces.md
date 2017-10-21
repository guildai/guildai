# Guild namespaces

A namespace is an optional leading component of a Guild package
reference that consists of a package term (i.e. terms that are
unmodified by `pkg_sources.safe_name`) that is separated from the rest
of the package reference with '/'. Namespaces are used to:

- Fully qualify package names so they unambiguously refer to a package
  distribution

- Provide information that can be used to install a package using pip

Examples of namespaces in package names:

    pypi/mnist
    gpig/mnist
    ./mnist

Each of these fully qualified package names refers to a different
package. The first refers to the `mnist` project on PyPI. The second
refers to `gpkg.mnist` on PyPI. The third refers to a local modelfile
distribution in a directory named `mnist`.

Guild namespaces are manged with the `guild.namespace` module:

    >>> from guild import namespace

Namespaces can be registered by installing packages that provide entry
points for the "guild.namespaces" group. For these tests, we want to
ensure we are only working with built-ins:

    >>> namespace.limit_to_builtin()

We can use `iter_namespaces` to list the supported namespaces:

    >>> sorted(namespace.iter_namespaces())
    [('gpkg', <guild.namespace.Namespace 'gpkg'>),
     ('modelfile', <guild.namespace.Namespace 'modelfile'>),
     ('pypi', <guild.namespace.Namespace 'pypi'>)]

We can use `for_name` to lookup namespaces by name:

    >>> pypi = namespace.for_name("pypi")
    >>> gpkg = namespace.for_name("gpkg")

If a name isn't registered as a namespace, `for_name` raises a lookup
error:

    >>> namespace.for_name("other")
    Traceback (most recent call last):
    LookupError: other

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

    >>> pypi.pip_install_info("mnist")
    ('mnist', ['https://pypi.python.org/simple'])

    >>> gpkg.pip_install_info("mnist")
    ('gpkg.mnist', ['https://pypi.python.org/simple'])

Here we see that, under the `pypi` namespace, `mnist` refers to the
same project name whereas, under `gpkg`, it refers to `gpkg.mnist`.

## Pip project name membershiup

Namespaces can be used to test if a pip project name is a member using
`is_project_name_member`. Namespace membership falls into one of three
values:

- "yes", the project name is a member of the namespace
- "no", the project name is not a member
- "maybe", the project name might be a member

In addition to membership, the test returns the Guild package name
that references the pip project under the namespace.

Let's test the `mnist` package:

    >>> pypi.is_project_name_member("mnist")
    ('maybe', 'pypi/mnist')

    >>> gpkg.is_project_name_member("mnist")
    ('no', None)

Here we see that the package `mnist` might be a member of the `pypi`
namespace and if it is would be named `pypi/mnist` under the
namespace. The package is not however a member of the `gpkg`
namespace.

Let's test `gpkg.mnist`:

    >>> pypi.is_project_name_member("gpkg.mnist")
    ('maybe', 'pypi/gpkg.mnist')

    >>> gpkg.is_project_name_member("gpkg.mnist")
    ('yes', 'mnist')

Here we see that the project name `gpkg.mnist` might be a member of
the `pypi` namespace and would be named `pypi/gpig.mnist` if it
is. However, `gpkg` is laying full claim to the project and names it
`mnist`.

## Modelfile namespace

Guild provides a special namespace for modelfile packages. A modelfile
package is a local directory containing a modelfile (i.e. a file named
`MODEL` or `MODELS`). If a modelfile package is on the Python path,
Guild will see any models defined in it.

    >>> modelfile = namespace.for_name("modelfile")

Modelfile packages cannot be installed using pip:

    >>> modelfile.pip_install_info("mnist")
    Traceback (most recent call last):
    TypeError: modelfiles cannot be installed using pip

However, they can be used to test project name membership and
translate a modelfile project name into a package name.

Modefile project names are in the format:

    '.modelfile.' + ESCAPED_PROJECT_NAME

Project names are escaped because they may contain 'unsafe' character
that are disallowed in standard project names.

Any project name that doesn't start with '.modelfile.' is not
considered a member:

    >>> modelfile.is_project_name_member("mnist")
    ('no', None)

    >>> modelfile.is_project_name_member("gpkg.mnist")
    ('no', None)

Let's create a modefile project name. We'll need a helper:

    >>> from guild.model import escape_project_name

And our project name:

    >>> modelfile_project = ".modelfile." + escape_project_name("foo/bar")

Let's test it!

    >>> modelfile.is_project_name_member(modelfile_project)
    ('yes', 'foo/bar')

Here we see that our modelfile project name is the `foo/bar` package.

For more information about modelfile package names, see the [packages
test](packages.md).

## Applying namespaces

The function `apply_namespace` can be used to apply a namespace to a
project name and return a package name:

    >>> namespace.apply_namespace("mnist")
    'pypi/mnist'

    >>> namespace.apply_namespace("gpkg.mnist")
    'mnist'
