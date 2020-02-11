# Guild Example: `package`

This example modifies the [hello](../hello/README.md) example to
include support for packaging.

- [guild.yml](guild.yml) - Project Guild file
- [say.py](say.py) - Prints a greeting
- [cat.py](cat.py) - Prints contents of a file
- [hello.txt](hello.txt) - Sample file used by `hello-file` operation

The Guild file is modified to support packaging with modifications:

- Promote the Guild file format from _operation only_ to _full_
  format. This moves the operations under a model definition. We use
  the anonymous model (named with an empty string) to maintain the
  original interface.

- Add a `package` top-level object to the Guild file. This defines the
  package name and defines the data files that should be included in
  the package.

With package support, the `hello-file` operation can be run on remote
servers. Without this change, the file `hello.txt` would not be
included in the package installed on remote systems.

All of the steps outlined in the [hello](../hello/README.md) can be
run with this example on a remote. Include the additional option
`--remote NAME` for each command that you want to run remotely.

## Build a Package

From the `package` example directory, run:

```
$ guild package
```

## Create a Virtual Environment

To ensure that this example does not affect your system Python
environments, create a virtual environment.

You can use `guild init`, `virtualenv`, or `conda`. This example below
uses `guild init`.

From the `package` example directory, run:

```
$ guild init -y
```

Activate the environment:

```
$ source guild-env
```

If you use `virtual` or `conda` to create a virtual environment,
activate the environment as directed.

## Install the Package

Use `pip` to install the package.

```
$ pip install dist/*
```

List installed Guild packages:

```
$ guild packages
hello  0.1  Sample package
```

You can also see the installed packages when running `pip list` and
`pip info` (Guild packages are standard Python packages).

## Use the Package

Once installed, operations defined in the package are available
anywhere on the system -- even if the project director is removed.

```
$ guild run gpkg.hello/hello
```

By default, Guild does not include package operations when listing
operations from a project directory.

From the `package` directory, show available operations:

```
guild operations
hello       Say hello to my friends
hello-file  Shows a message from a file
hello-op    Show a message from a hello-file operation
```

Include installed operations in the list by specifying the
`--installed` option:

```
$ guild operations --installed
gpkg.hello/hello       Say hello to my friends
gpkg.hello/hello-file  Shows a message from a file
gpkg.hello/hello-op    Show a message from a hello-file operation
hello                  Say hello to my friends
hello-file             Shows a message from a file
hello-op               Show a message from a hello-file operation
```

Change to the parent directory:

```
cd ..
```

From the parent directory, show operations:

```
$ guild operations
gpkg.hello/hello       Say hello to my friends
gpkg.hello/hello-file  Shows a message from a file
gpkg.hello/hello-op    Show a message from a hello-file operation
```

Guild shows installed operations because the parent directory does not
contain a Guild file.

Run a packaged operation from the parent directory:

```
$ guild run hello msg="hi from a packaged operation"
```
