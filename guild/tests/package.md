# Packaging

Guild supports the creation of Guild-specific *packages*. A package is
a Python wheel distribution and can be installed using any tool that
supports installing that format.

For these tests, we'll use a writable directory, which will contain
our project files and generated files.

    >>> project = mkdtemp()

Copy project files from the sample `package` project.

    >>> project_src = sample("projects", "package")

    >>> for name in ["guild.yml", "README.md", "a.txt", "train.py"]:
    ...     copyfile(path(project_src, name), path(project, name))

    >>> find(project)
    README.md
    a.txt
    guild.yml
    train.py

Packages are built from guildfiles. Packages contain the guildfile and
other required files.

The package we'll build is defined in the project guildfile. Let's
load that.

    >>> use_project(project)
    >>> gf = guildfile.for_dir(".")

The package definition for a Guild file is accessed with the `package`
attribute.

    >>> pkg = gf.package

Packages specify how to build the package. Here are some attributes:

    >>> pkg.name
    'gpkg.hello'

    >>> pkg.version
    '0.3.0.dev4'

    >>> pkg.url
    'https://github.com/guildai/index/tree/master/hello'

    >>> pkg.author_email
    'packages@guild.ai'

The `package` command generates a Python wheel using the package
definition in the Guild file.

    >>> IGNORE = ["package init file", "byte-compiling is disabled"]

    >>> run("guild package", ignore=IGNORE)  # doctest: +REPORT_UDIFF
    running bdist_wheel
    running build
    running build_py
    creating build
    creating build/lib
    creating build/lib/gpkg
    creating build/lib/gpkg/hello
    copying ./train.py -> build/lib/gpkg/hello
    copying ./a.txt -> build/lib/gpkg/hello
    copying ./guild.yml -> build/lib/gpkg/hello
    copying ./README.md -> build/lib/gpkg/hello
    installing to build/.../wheel
    running install
    running install_lib
    copying gpkg/hello/train.py -> build/.../wheel/gpkg/hello
    copying gpkg/hello/a.txt -> build/.../wheel/gpkg/hello
    copying gpkg/hello/README.md -> build/.../wheel/gpkg/hello
    copying gpkg/hello/guild.yml -> build/.../wheel/gpkg/hello
    running install_egg_info
    running egg_info
    writing gpkg.hello.egg-info/PKG-INFO
    writing dependency_links to gpkg.hello.egg-info/dependency_links.txt
    writing entry points to gpkg.hello.egg-info/entry_points.txt
    writing namespace_packages to gpkg.hello.egg-info/namespace_packages.txt
    writing top-level names to gpkg.hello.egg-info/top_level.txt
    writing manifest file 'gpkg.hello.egg-info/SOURCES.txt'
    reading manifest file 'gpkg.hello.egg-info/SOURCES.txt'
    writing manifest file 'gpkg.hello.egg-info/SOURCES.txt'
    Copying gpkg.hello.egg-info to build/.../wheel/gpkg.hello-0.3.0.dev4...egg-info
    Installing build/.../wheel/gpkg.hello-0.3.0.dev4...-nspkg.pth
    running install_scripts
    creating build/.../wheel/gpkg.hello-0.3.0.dev4...dist-info/WHEEL
    creating 'dist/gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl' and adding 'build/.../wheel' to it
    adding 'gpkg.hello-0.3.0.dev4...-nspkg.pth'
    adding 'gpkg/hello/README.md'
    adding 'gpkg/hello/a.txt'
    adding 'gpkg/hello/guild.yml'
    adding 'gpkg/hello/train.py'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/METADATA'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/PACKAGE'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/WHEEL'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/entry_points.txt'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/namespace_packages.txt'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/top_level.txt'
    adding 'gpkg.hello-0.3.0.dev4.dist-info/RECORD'
    removing build/.../wheel

The wheel is written to the `dist` subdirectory.

    >>> find("dist")
    gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl

Wheels are zip files. We can read the contents of the generated file.

    >>> import zipfile
    >>> wheel_path = path("dist", "gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl")
    >>> wheel = zipfile.ZipFile(wheel_path)
    >>> pprint(sorted(wheel.namelist()))  # doctest: +REPORT_UDIFF
    ['gpkg.hello-0.3.0.dev4...-nspkg.pth',
     'gpkg.hello-0.3.0.dev4.dist-info/METADATA',
     'gpkg.hello-0.3.0.dev4.dist-info/PACKAGE',
     'gpkg.hello-0.3.0.dev4.dist-info/RECORD',
     'gpkg.hello-0.3.0.dev4.dist-info/WHEEL',
     'gpkg.hello-0.3.0.dev4.dist-info/entry_points.txt',
     'gpkg.hello-0.3.0.dev4.dist-info/namespace_packages.txt',
     'gpkg.hello-0.3.0.dev4.dist-info/top_level.txt',
     'gpkg/hello/README.md',
     'gpkg/hello/a.txt',
     'gpkg/hello/guild.yml',
     'gpkg/hello/train.py']

Use `twine` to check the generated distribution.

    >>> from twine.commands import check
    >>> dist_path = path("dist", "gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl")
    >>> check.check([dist_path])
    Checking dist/gpkg.hello-0.3.0.dev4-py2.py3-none-any.whl: PASSED
    False

## Default packages

If a package def isn't specified, Guild will use the name of the
default model as the package name.

Create a project with a Guild file that does not contain a package def.

    >>> cd(mkdtemp())
    >>> write("guild.yml", """
    ... - model: test
    ... """)

Generate a package for it.

    >>> run("guild package")
    ???
    <exit 0>

    >>> find("dist")
    test-0.0.0-py2.py3-none-any.whl

List the package contents.

    >>> wheel_path = path("dist", "test-0.0.0-py2.py3-none-any.whl")
    >>> wheel = zipfile.ZipFile(wheel_path)
    >>> pprint(sorted(wheel.namelist()))  # doctest: +REPORT_UDIFF
    ['test-0.0.0.dist-info/METADATA',
     'test-0.0.0.dist-info/PACKAGE',
     'test-0.0.0.dist-info/RECORD',
     'test-0.0.0.dist-info/WHEEL',
     'test-0.0.0.dist-info/entry_points.txt',
     'test-0.0.0.dist-info/namespace_packages.txt',
     'test-0.0.0.dist-info/top_level.txt',
     'test/guild.yml']

Use the `--clean` option to delete build artifacts before creating a
package.

    >>> run("guild package --clean", ignore=["does not exist"])  # doctest: +REPORT_UDIFF
    running clean
    removing 'build/lib' (and everything under it)
    removing 'build/bdist.linux-x86_64' (and everything under it)
    removing 'build'
    ...
    <exit 0>

If a Guild file doesn't contain a package def or a model def, it
creates a package named 'gpkg.anonymous_DIGEST'.

    >>> cd(mkdtemp())
    >>> write("guild.yml", """
    ... - config: test
    ... """)

    >>> run("guild package")
    WARNING: package name not defined in ./guild.yml - using gpkg.anonymous_...
    running bdist_wheel
    running build
    ...
    <exit 0>

## Project based error messages

A project must have a Guild file to be packaged.

    >>> cd(mkdtemp())

    >>> run("guild package")
    guild: the current directory does not contain a guild.yml file
    guild.yml is required when creating a package. Create one in this
    directory first or try specifying a different directory.
    <exit 1>

## Name conflicts with local Python packages

The package name in the Guild file generates a unique Python package,
which contains the project data files. If a local Python package
exists with the same name, Guild `package` fails with an error
message.

We use the `package-name-conflict` project to illustrate.

    >>> use_project("package-name-conflict")

    >>> run("guild package")
    guild: package name 'foo' in guild.yml conflicts with Python
    package 'foo'
    Provide a unique package name in guild.yml and try again.
    <exit 1>
