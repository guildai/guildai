# Packaging

Packaging is supported by the `guild.package` module.

    >>> import guild.package

For these tests, we'll use a writable directory, which will contain
our project files and generated files.

    >>> workspace = mkdtemp()
    >>> dir(workspace)
    []

Packages are built from guildfiles. The contain the guildfile and
other files needed by the package.

We'll create a package from the sample project
[package](samples/projects/package). Let's setup our workspace by
linking to the project files.

    >>> for name in ["guild.yml", "README.md", "a.txt", "train.py"]:
    ...   symlink(abspath(join_path(sample("projects/package"), name)),
    ...           join_path(workspace, name))

Our workspace:

    >>> dir(workspace)
    ['README.md', 'a.txt', 'guild.yml', 'train.py']

The package we'll build is defined in the project guildfile. Let's
load that.

    >>> gf = guildfile.for_dir(workspace)

We can access the package definition using the `package` attribute:

    >>> pkg = gf.package
    >>> pkg
    <guild.guildfile.PackageDef 'gpkg.hello'>

Packages have various attributes that are used to create the package.

    >>> pkg.name
    'gpkg.hello'

    >>> pkg.version
    '0.3.0.dev4'

    >>> pkg.url
    'https://github.com/guildai/index/tree/master/hello'

    >>> pkg.author_email
    'packages@guild.ai'

We can use `guild.package.create_package` to build a binary wheel
distribution for our package.

Let's create the package:

    >>> out = guild.package.create_package(gf.src, capture_output=True)
    >>> print("-\n" + out.decode("UTF-8"))
    -...
    running bdist_wheel
    running build
    running build_py
    ...
    <BLANKLINE>

Here's our distribution:

    >>> files = dir(join_path(workspace, "dist"))
    >>> files
    ['gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl']

And its contents:

    >>> import zipfile
    >>> wheel = zipfile.ZipFile(join_path(workspace, "dist", files[0]))
    >>> pprint(sorted(wheel.namelist()))
    [...
     'gpkg/hello/README.md',
     'gpkg/hello/a.txt',
     'gpkg/hello/guild.yml',
     'gpkg/hello/train.py']

Use `twine` to check the generated distribution:

    >>> from twine.commands import check
    >>> dist_path = join_path(
    ...     workspace, "dist",
    ...     "gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl")
    >>> check.check([dist_path])
    Checking .../dist/gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl: PASSED
    False

## Default packages

If a package def isn't specified, Guild will use the name of the
default model as the package name.

Let's create a new workspace:

    >>> workspace = mkdtemp()
    >>> dir(workspace)
    []

And create a sample Guild file in it that contains only a model def:

    >>> write(join_path(workspace, "guild.yml"), """
    ... - model: test
    ... """)

And generate a package for it:

    >>> gf = guildfile.for_dir(workspace)
    >>> out = guild.package.create_package(gf.src, capture_output=True)
    >>> print(out.decode("UTF-8"))
    running bdist_wheel
    running build
    running build_py
    ...
    adding 'test/guild.yml'
    adding 'test-0.0.0.dist-info/...'
    ...
    <BLANKLINE>

The generated files::

    >>> files = dir(join_path(workspace, "dist"))
    >>> files
    ['test-0.0.0-py2.py3-none-any.whl']

And the package contents:

    >>> wheel = zipfile.ZipFile(join_path(workspace, "dist", files[0]))
    >>> pprint(sorted(wheel.namelist()))
    [...
     'test/guild.yml']

Use the `clean` option to delete build artifacts before creating a
package.

    >>> out = guild.package.create_package(gf.src, clean=True, capture_output=True)
    >>> print(out.decode("UTF-8"))
    running clean
    removing 'build/lib...' (and everything under it)
    removing 'build/bdist...' (and everything under it)
    'build/scripts...' does not exist -- can't clean it
    removing 'build'
    running bdist_wheel
    running build
    running build_py
    ...

If a Guild file doesn't contain a package def or a model def, it
creates a package named 'gpkg.anonymous_DIGEST':

    >>> workspace = mkdtemp()
    >>> dir(workspace)
    []

    >>> write(join_path(workspace, "guild.yml"), """
    ... - config: test
    ... """)
    >>> gf = guildfile.for_dir(workspace)

    >>> out = guild.package.create_package(gf.src, capture_output=True)
    >>> print(out.decode())
    WARNING: package name not defined in .../guild.yml - using gpkg.anonymous_...
    running bdist_wheel
    running build
    running build_py
    ...
    adding 'gpkg/anonymous_.../guild.yml'
    adding 'gpkg.anonymous_...-0.0.0.dist-info/...'
    ...

## Project based error messages

A project must have a Guild file to be packaged.

    >>> workspace = mkdtemp()
    >>> dir(workspace)
    []

    >>> Project(workspace).package()  # doctest: -NORMALIZE_PATHS
    Traceback (most recent call last):
    SystemExit: ("'...' does not contain a guild.yml
    file\nA guild.yml file is required when creating a package.
    Create one in this directory first or try specifying a different
    directory.", 1)

A project must exist:

    >>> Project("NOT_EXISTS").package()  # doctest: -NORMALIZE_PATHS
    Traceback (most recent call last):
    SystemExit: ("'NOT_EXISTS' does not exist\nTry specifying a
    different directory.", 1)

## Name conflicts with local Python packages

The package name in the Guild file generates a unique Python package,
which contains the project data files. If a local Python package
exists with the same name, Guild `package` fails with an error
message.

We use the `package-name-conflict` project to illustrate.

    >>> project = Project(sample("projects/package-name-conflict"))
    >>> project.package()
    Traceback (most recent call last):
    SystemExit: (1, "guild: package name 'foo' in guild.yml conflicts with
    Python package 'foo'...Provide a unique package name in guild.yml and
    try again...")
