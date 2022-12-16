# Python Path

These tests illustrate how Guild configures the Python system path
under various scenarios.

## Python path default behavior (background)

When run as `python <file>`, Python inserts the parent directory of
`<file>` into the system path as the first entry. The path specified
by the environment variable `PYTHONPATH` is split on `os.path.pathsep`
and each entry is inserted into the system path after the first entry
(the file parent directory). Subsequent entries in the system path are
used to locate standard Python modules.

However, when a main module is run with the `-m` option, the first
path entry is the current directory . This allows modules to be run
without specifying `PYTHONPATH` provided they're defined relative to
the current directory.

For a detailed explanation see [The initialization of the sys.path
module search
path](https://docs.python.org/3/library/sys_path_init.html).

## Guild modified behavior

Guild inserts various additional paths into the system path when it
runs a Python based operation. These include, in order of appearance
in the system path:

- Operation source code root directory
- Path defined by `PYTHONPATH` env defined for the operation (e.g. see
  [guild.yml](guild.yml))
- The OS process `PYTHONPATH` environment variable set for the Guild
  process that starts the Python operation

These are specified by setting the `PYTHONPATH` environment variable
for the operation process. They therefore appear in the operation
system path starting with the second entry and being followed by the
standard Python module paths.

## Test setup

We use the `pythonpath` sample project for our tests.

    >>> project = Project(sample("projects", "pythonpath"))

    >>> cd(sample("projects", "pythonpath"))

Isolate runs in a new Guild home:

    >>> set_guild_home(mkdtemp())

This project provides operations that print the value of `sys.path` as
a JSON encoded string to standard output.

    >>> run("guild ops")
    default
    pkg
    pkg-with-subdir
    pythonpath-env
    sourcecode-dest
    sourcecode-disabled
    subdir

We use a helper that generates a run for a specified operation and
returns the run and its decoded output.

    >>> def sys_path_for_op(op, extra_env=None, extra_args=None):
    ...     from guild import run as runlib
    ...
    ...     extra_args = " ".join([shlex_quote(arg) for arg in (extra_args or [])])
    ...     env = {"PYTHONPATH": ""}
    ...     if extra_env:
    ...         env.update(extra_env)
    ...     with Env(env):
    ...         out = run_capture(f"guild run {op} {extra_args} -y")
    ...     run_dir = run_capture("guild select --path")
    ...     return runlib.for_dir(run_dir), json.loads(out)

We also use a helper to assert path values.

    >>> def assert_path(actual, expected):
    ...     assert actual == expected, f"expected '{expected}' got '{actual}'"

It's important that the project location is not included in the system
path for a Python based operation. Here's a function that asserts that
for a given system path.

    >>> def assert_not_project(sys_path):
    ...     project_path = realpath(".")
    ...     assert not project_path in sys_path, (project_path, sys_path)

## Run script directly

When Guild runs a Python script directly, it uses `guild.op_main` as
an intermediary to process flag values and make them available to the
target script accoding to the `flags-dest` interface.

Generate a run for the `sys_path_test.py` script:

    >>> run, sys_path = sys_path_for_op("sys_path_test.py")

The command that Guild ran:

    >>> run.get("cmd")
    ['...python', '-um', 'guild.op_main', 'sys_path_test']

The `PYTHONPATH` env var is used to configure Python with the
appropriate system paths.

    >>> pythonpath = run.get("env").get("PYTHONPATH").split(os.path.pathsep)

We expect to have two entries in the result: one that locates the run
source code and another that locates the Guild package.

    >>> len(pythonpath)
    2

The first entry in the path is the source code root directory. It's
specified relative to the current directory. By default, the source
code root is the run directory itself.

    >>> assert_path(pythonpath[0], ".")

The second entry is the Guild package location.

    >>> assert_path(pythonpath[1], guild.__pkgdir__)

### sys.path

The first entry is the source code root. In this case, it's the run
directory.

    >>> assert_path(sys_path[0], run.dir)

The second entry the Guild package location.

    >>> assert_path(sys_path[1], guild.__pkgdir__)

It's important that the project directory is not in the the system
path for a Python operation. Project source code must be run from the
run directory exclusively.

    >>> assert_not_project(sys_path)

## Default operation

The `default` op runs the `test` module without additional
configuration. The behavior is the same as when running
`sys_path_test.py` diretly (above).

    >>> run, sys_path = sys_path_for_op("default")

Our standard verification:

    >>> assert_path(sys_path[0], run.dir)
    >>> assert_path(sys_path[1], guild.__pkgdir__)
    >>> assert_not_project(sys_path)

## Alternative source code destination

The `sourcecode-dest` operation configures the destination path for
source code. Guild uses this to copy operation source code to an
alternative location under the run directory. In this case, the
operation configures the target as `src`.

    >>> run, sys_path = sys_path_for_op("sourcecode-dest")

The first entry in `sys.path` is the source code root.

    >>> assert_path(sys_path[0], path(run.dir, "src"))

The remaining standard tests apply:

    >>> assert_path(sys_path[1], guild.__pkgdir__)
    >>> assert_not_project(sys_path)

The run directory itself is not in the path.

    >>> run.dir not in sys_path, run.dir, sys_path
    (True, ...)

## Use of PYTHONPATH process env

When `PYTHONPATH` is set in the calling process environment, it is
included *after* both the source code destination and the Guild
package location.

Let's include two paths in the process `PYTHONPATH` env as an example.

    >>> tmp1 = mkdtemp()
    >>> tmp2 = mkdtemp()

    >>> run, sys_path = sys_path_for_op(
    ...     "sys_path_test.py",
    ...     extra_env={"PYTHONPATH": os.path.pathsep.join([tmp1, tmp2])}
    ... )

The first two entries are the standard entries we've seen before.

    >>> assert_path(sys_path[0], run.dir)
    >>> assert_path(sys_path[1], guild.__pkgdir__)

The third and fourth entries are are two additional directories in the
order specified in the `PYTHONPATH` env var.

    >>> assert_path(sys_path[2], tmp1)
    >>> assert_path(sys_path[3], tmp2)

Confirm that the project is not in the path:

    >>> assert_not_project(sys_path)

## Use of operation env

An operation can define `PYTHONPATH` in `env` to specify entries that
are included *before* any other Python path locations. The
`pythonpath-env` operation illustrates this pattern. This operation
uses the flag `path` to configure its `env`.

We again use two directories in our configure path.

    >>> run, sys_path = sys_path_for_op(
    ...     "pythonpath-env",
    ...     extra_args=["path=" + os.path.pathsep.join([tmp1, tmp2])]
    ... )

The first two entries are the paths specified in the operation
`PYTHONPATH` env.

    >>> assert_path(sys_path[0], tmp1)
    >>> assert_path(sys_path[1], tmp2)

The third entry is the source code root.

    >>> assert_path(sys_path[2], run.dir)

The fourth entry is the Guild package location.

    >>> assert_path(sys_path[3], guild.__pkgdir__)

We again confirm that the project directory has not slipped into the
system path.

    >>> assert_not_project(sys_path)

## Disabling source code

When `sourcecode` is disabled, Guild omits the default run source code
directory from the Python path. We use the `sourcecode-disabled` to
illustrate.

When we run `sourcecode-disabled` without otherwise providing a path
to the source code, we get an error.

    >>> try:
    ...     sys_path_for_op("sourcecode-disabled")
    ... except RunError as e:
    ...     print(e.output)
    ... else:
    ...     assert False
    guild: No module named sys_path_test

Because we disabled source code copies for the operation, we must
provide the location of the `sys_path_test` module via the
`PYTHONPATH` env variable. In this case, we specify the project
directory (though this is an anti-pattern for best-practice).

    >>> run, sys_path = sys_path_for_op(
    ...     "sourcecode-disabled",
    ...     extra_env={"PYTHONPATH": realpath(".")})

As per the previous example where we specified `PYTHONPATH` for the
process environment, our first two system path entries are the source
code root and the Guild package location respectively.

    >>> assert_path(sys_path[0], run.dir)
    >>> assert_path(sys_path[1], guild.__pkgdir__)

The third entry is the path that we specified in the process
environment variable.

    >>> assert_path(sys_path[2], project.cwd)

## Python path and sub-directories

When an operation specifies a subdirectory for `main` in the format
`SUBDIR/MODULE`, Guild includes the subdirectory path in the Python
system path. The `subdir` operation illustrates this. It's `main` spec
is `src/sys_path_test2.py`.

    >>> run, sys_path = sys_path_for_op("subdir")

The command that was run for the operation:

    >>> run.get("cmd")
    ['...python', '-um', 'guild.op_main', 'src/sys_path_test2', '--']

The module `guild.op_main` uses the spec `src/sys_path_test2` to
locate the target module under the `src` directory. It modifies the
system path to include the additional `src` subdirectory.

The first entry is the source code root.

    >>> assert_path(sys_path[0], run.dir)

The second entry is the `src` source code subdirectory.

    >>> assert_path(sys_path[1], path(run.dir, "src"))

NOTE: This is arguably an incorrect implementation. The calling
process is otherwise configuring Python path entries to successfully
run the specified Python module. `op_main` should not have to handle
path configuration but should serve as a straight forward pass-through
to the Python module loading facility. In this case, the source code
root should probably not be included in the path. This would be the
responsibility of the process configuration to setup `PYTHONPATH` and
not for `op_main`.

The third entry is the Guild package location:

    >>> assert_path(sys_path[2], guild.__pkgdir__)

The project directory does not appear in the system path.

    >>> assert_not_project(sys_path)

## Python packages

When a Python package is specified in `main` --
e.g. `pkg.sys_path_test3` -- Guild does not need to insert additional
system paths as with subdirectories (see above). The `pkg` operation
illustrates.

The `pkg` subdirectory contains `__init__.py`, which tells Python it's
a package.

    >>> pkg_files = dir(path(project.cwd, "pkg"))
    >>> "__init__.py" in pkg_files, pkg_files
    (True, ...)

Run the operation:

    >>> run, sys_path = sys_path_for_op("pkg")

The system path contains the standard locations.

    >>> assert_path(sys_path[0], run.dir)
    >>> assert_path(sys_path[1], guild.__pkgdir__)
    >>> assert_not_project(sys_path)

## Python packages with subdirectories

This test shows Guild's behavior when a package module is located
within a project subdirectory. We use the `pkg-with-subdir` operation
to illustrate.

    >>> run, sys_path = sys_path_for_op("pkg-with-subdir")

Here we see that `op_main` inserts the `src2` subdirectory into the
system path as it did in with the `subdir` operation.

    >>> assert_path(sys_path[0], run.dir)
    >>> assert_path(sys_path[1], path(run.dir, "src2"))
    >>> assert_path(sys_path[2], guild.__pkgdir__)
    >>> assert_not_project(sys_path)

## Non-Python opertion

Non-Python operations do not define `PYTHONPATH`.

Run `non_python` (a shell script) with env that resets any current
`PYTHONPATH` value from the test env.

    >>> with Env({"PYTHONPATH": ""}):  # doctest: -WINDOWS
    ...     print(run_capture("guild run non_python -y"))
    PYTHONPATH:
