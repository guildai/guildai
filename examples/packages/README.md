# Guild Example: `packages`

This examples shows how Guild is used to package and distribute
operations.

- [a/guild.yml](a/guild.yml) - Guild file for package a
- [a/train.py](a/train.py) - Sample script for package a
- [b/guild.yml](b/guild.yml) - Guild file for package b
- [b/train.py](b/train.py) - Sample script for package b

Run the steps below to build, install, and use packages `a` and `b`.

## Build Packages

From the `packages` example directory, run the commands below.

**IMPORTANT:** The two commands below require that you run from a
terminal shell that supports
[subshells](https://www.tldp.org/LDP/abs/html/subshells.html) using
`(...)` syntax. *bash* on Linux and macOS support this. If you are
running on Windows, change to each directory below and run the
applicable command from the sub-directory.

Build package `a`:

```
$ (cd a && guild package)
```

Build package `b`:

```
$ (cd b && guild package)
```

## Create a Virtual Environment

To ensure that these examples do not effect your system or user Python
environments, create a virtual environment.

You can use `guild init`, `virtualenv`, or `conda`.

This example below uses `guild init`.

From the `packages` example directory, run:

```
$ guild init -y
```

Activate the environment:

```
$ source guild-env
```

If you use `virtual` or `conda` to create a virtual environment,
activate the environment as directed.

## Install Packages

Use `pip` to install the packages created for `a` and `b`.

```
$ pip install a/dist/*
$ pip install b/dist/*
```

Note that packages are named `gpkg.a` and `gpkg.b` respectively. These
values are defined in the Guild files for the respective directories.
This is a naming convention used for Guild packages and is not
strictly required.

List installed Guild packages:

```
$ guild packages
gpkg.a  0.0.0  Sample package
gpkg.b  0.0.0  Sample package
```

You can also see the installed packages when running `pip list` and
`pip info` (Guild packages are standard Python packages).

## Use the Package

Once installed, the models and operations defined for `a` and `b` are
available.

List models:

```
$ guild models
gpkg.a/a
gpkg.b/b
```

List operations:

```
$ guild operations
gpkg.a/a:train
gpkg.b/b:train
```

Run `a:train`:

```
$ guild run a:train
You are about to run gpkg.a/a:train
Continue? (Y/n)
```

Press `Enter` to start the operation. Guild runs
[`a/train.py`](a/train.py).

Run `b:train`:

```
$ guild run b:train
You are about to run gpkg.b/b:train
Continue? (Y/n)
```

Press `Enter` to start the operation. Guild similarly runs
[`b/train.py`](b/train.py).

Install package operations may be run from any directory.

When listing models and operations from a project directory (i.e. a
directory that contains a Guild file), package models and operations
are not shown by default. To view package models and operations, use
the `--installed` option for the applicable command.

For example, when listing operations from within the `a` directory,
Guild will not show installed operations because a Gulid file
(`guild.yml`) exists. To show all operations, run:

```
$ guild operations --installed
```
