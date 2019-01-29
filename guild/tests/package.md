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
[samples/projects/package](samples/projects/package). Let's setup our
workspace by linking to the project files.

    >>> for name in ["guild.yml", "README.md", "a.txt"]:
    ...   symlink(abspath(join_path(sample("projects/package"), name)),
    ...           join_path(workspace, name))

Our workspace:

    >>> dir(workspace)
    ['README.md', 'a.txt', 'guild.yml']

The package we'll build is defined in the project guildfile. Let's
load that.

    >>> gf = guildfile.from_dir(workspace)

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
     'gpkg/hello/guild.yml']

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

    >>> gf = guildfile.from_dir(workspace)
    >>> out = guild.package.create_package(gf.src, capture_output=True)
    >>> print("-\n" + out.decode("UTF-8"))
    -
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

If a Guild file doesn't contain a package def or a model def, it
creates a package named 'package':

    >>> workspace = mkdtemp()
    >>> dir(workspace)
    []

    >>> write(join_path(workspace, "guild.yml"), """
    ... - config: test
    ... """)
    >>> gf = guildfile.from_dir(workspace)

    >>> out = guild.package.create_package(gf.src, capture_output=True)
    >>> print("-\n" + out.decode("UTF-8"))
    -
    running bdist_wheel
    running build
    running build_py
    ...
    adding 'package/guild.yml'
    adding 'package-0.0.0.dist-info/...'
    ...
    <BLANKLINE>
