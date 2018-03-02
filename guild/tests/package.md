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

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(workspace)

We can access the package definition using the `package` attribute:

    >>> pkg = gf.package
    >>> pkg
    <guild.guildfile.PackageDef 'hello'>

Packages have various attributes that are used to create the package.

    >>> pkg.name
    'hello'

    >>> pkg.version
    '0.3.0.dev4'

    >>> pkg.url
    'https://github.com/guildai/index/tree/master/hello'

    >>> pkg.maintainer_email
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
    >>> pprint(sorted(wheel.namelist())) # doctest: +REPORT_UDIFF
    ['gpkg.hello-0.3.0.dev4.dist-info/DESCRIPTION.rst',
     'gpkg.hello-0.3.0.dev4.dist-info/METADATA',
     'gpkg.hello-0.3.0.dev4.dist-info/PACKAGE',
     'gpkg.hello-0.3.0.dev4.dist-info/RECORD',
     'gpkg.hello-0.3.0.dev4.dist-info/WHEEL',
     'gpkg.hello-0.3.0.dev4.dist-info/metadata.json',
     'gpkg.hello-0.3.0.dev4.dist-info/namespace_packages.txt',
     'gpkg.hello-0.3.0.dev4.dist-info/top_level.txt',
     'gpkg/hello/README.md',
     'gpkg/hello/a.txt',
     'gpkg/hello/guild.yml']
