---
doctest: +R +FIXME_CI
---

# R Script

These tests use the `r-script` sample project.

    >>> use_project("r-script")

Run an empty R script.

    >>> run("guild run empty.R -y")
    <exit 0>

Run a simple R script.

    >>> run("guild run simple.R -y")
    > noise = 3
    > layers <- 32L
    > layers = 4
    > name = "foo"
    > skip_connections = TRUE

## R version and Guild check

The user can use `check` to show R package

    >>> run("guild check --r-script")
    ???
    rscript_version:           ...
    <exit 0>

## R not installed

When R is not installed, operations that require R (e.g. running an R
script) fail with an error message.

Use `guild_patch.py` in a temp project to modify Guild to simulate R
not being installed.

    >>> tmp = mkdtemp()

    >>> cd(tmp)
    >>> write("guild_patch.py", """
    ... from guild import util
    ...
    ... def which_no_r(s):
    ...     if s == "Rscript":
    ...         return None
    ...
    ... util.which = which_no_r
    ... """)

Create an empty R script to run.

    >>> touch("empty.R")

Try to run the script.

    >>> run("guild run empty.R -y")
    guild: cannot run 'empty.R': R is not installed on this system.
    Refer to https://www.r-project.org/ for details.
    <exit 1>

## R package not installed

If the `guildai` R package is not installed or is too old, Guild
cannot run R scripts and will exit with an error message.

Use `guild_patch.py` again to modify Guild to simulate package check
behavior.

Guild handles two cases:

- `guildai` package is not installed
- `guildai` package is too old

### R package not installed

Simulate the package not being installed by returning an empty string
for `r_util.r_package_version`.

    >>> write("guild_patch.py", """
    ... from guild.plugins import r_util
    ...
    ... def package_not_installed():
    ...     return ""
    ...
    ... r_util.r_package_version = package_not_installed
    ... """)

Run the R script.

    >>> run("guild run empty.R -y")
    guild: cannot run 'empty.R': R package 'guildai' is not installed
    Install it by running 'guild run r-script:init' and try again.
    <exit 1>

### R package too old

Simulate the R package being too old.

    >>> write("guild_patch.py", """
    ... from guild.plugins import r_util
    ...
    ... def package_too_old():
    ...     return "0.0.0.9000"
    ...
    ... r_util.r_package_version = package_too_old
    ... """)

Run the R script.

    >>> run("guild run empty.R -y")
    guild: cannot run 'empty.R': R package 'guildai' is too old
    (got version '0.0.0.9000)'
    Upgrade the package by running 'guild run r-script:init' and
    try again.
    <exit 1>

## Run from subdirectory

TODO
