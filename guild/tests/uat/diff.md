# Diff

Create a project to generate runs we can diff. We use the `echo`
command below to show the different paths used for each diff scenario
so the operation doesn't need to do anything fancy.

    >>> project_dir = path(mkdtemp(), "diff-test-project")
    >>> ensure_dir(project_dir)
    >>> write(
    ...     path(project_dir, "hello.py"),
    ...     "import os; print('hello from %s' % os.getenv('RUN_ID'))"
    ... )

We also define an operation with an alternative source code dest for
source code related tests below.

    >>> write(
    ...     path(project_dir, "guild.yml"), """
    ... op:
    ...   main: hello
    ...   sourcecode:
    ...     dest: .
    ... """)

Delete existing runs.

    >>> quiet("guild runs rm -y")

Change to the project dir.

    >>> cd(project_dir)

Run the sample script twice.

    >>> run("guild run hello.py -y --run-id aaaa")
    hello from aaaa
    <exit 0>

    >>> run("guild run hello.py -y --run-id bbbb")
    hello from bbbb
    <exit 0>

Run the defined op once.

    >>> run("guild run op -y --run-id cccc")
    hello from cccc
    <exit 0>

Our runs:

    >>> run("guild runs")
    [1:cccc]  op        ...  completed
    [2:bbbb]  hello.py  ...  completed
    [3:aaaa]  hello.py  ...  completed
    <exit 0>

Source code for latest hello.py:

    >>> run("guild ls --sourcecode -Fo hello.py")
    ???/.guild/runs/bbbb/.guild/sourcecode:
      guild.yml
      hello.py
    <exit 0>

Source code for op run (uses an alternative source code dest):

    >>> run("guild ls --sourcecode -Fo op")
    ???/.guild/runs/cccc:
      guild.yml
      hello.py
    <exit 0>

## Default

Without args, `diff` runs on the latest two run directories. Run dir
args are ordered as run index `2` and run index `1` so that the latest
run is the right-most argument.

    >>> run("guild diff -c echo")
    ???/.guild/runs/bbbb .../.guild/runs/cccc
    <exit 0>

## Run Args

Guild presents the run directories to the diff command in the order
specified by the user.

    >>> run("guild diff -c echo 1 2")
    ???/.guild/runs/cccc .../.guild/runs/bbbb
    <exit 0>

    >>> run("guild diff -c echo 2 1")
    ???/.guild/runs/bbbb .../.guild/runs/cccc
    <exit 0>

    >>> run("guild diff -c echo aaa bbb")
    ???/.guild/runs/aaaa .../.guild/runs/bbbb
    <exit 0>

If only one run arg is provided, Guild exits with an error message.

    >>> run("guild diff -c echo 1")
    guild: diff requires two runs
    Try specifying a second RUN or 'guild diff --help' for more information.
    <exit 1>

## Paths

Path arg can be specified, which cause Guild to execute the diff
command for each path.

    >>> run("guild diff -c echo -p foo")
    ???/.guild/runs/bbbb/foo .../.guild/runs/cccc/foo
    <exit 0>

    >>> run("guild diff --cmd echo -p foo --path bar")
    ???/.guild/runs/bbbb/foo .../.guild/runs/cccc/foo
    .../.guild/runs/bbbb/bar .../.guild/runs/cccc/bar
    <exit 0>

## Base Dir

The `--dir` option can be used to compare a single run to a
directory.

Guild diffs the latest run by default.

    >>> run("guild diff -c echo --dir ./foo")
    ???/.guild/runs/cccc ./foo
    <exit 0>

Paths are applied to the specified dir.

    >>> run("guild diff -c echo --dir ./foo -p bar -p baz")
    ???/.guild/runs/cccc/bar ./foo/bar
    .../.guild/runs/cccc/baz ./foo/baz
    <exit 0>

    >>> run("guild diff -c echo bbbb --dir ./foo -p bar -p baz")
    ???/.guild/runs/bbbb/bar ./foo/bar
    .../.guild/runs/bbbb/baz ./foo/baz
    <exit 0>

A second run cannot be specified when using `--dir`.

    >>> run("guild diff -c echo bbbb cccc --dir ./foo")
    guild: cannot specify second RUN and --dir
    <exit 1>

## Source Code

If `--sourcecode` is specified, the compared dirs use the source code
directory associated with the run. Note that run `cccc` defined an
alternative source code dest (run dir root).

    >>> run("guild diff --cmd echo --sourcecode")
    ???/.guild/runs/bbbb/.guild/sourcecode .../.guild/runs/cccc
    <exit 0>

    >>> run("guild diff --cmd echo --sourcecode cccc bbbb")
    ???/.guild/runs/cccc .../.guild/runs/bbbb/.guild/sourcecode
    <exit 0>

Diff source code with paths.

    >>> run("guild diff --cmd echo --sourcecode -p hello.py -p guild.yml")
    ???/.guild/runs/bbbb/.guild/sourcecode/hello.py .../.guild/runs/cccc/hello.py
    .../.guild/runs/bbbb/.guild/sourcecode/guild.yml .../.guild/runs/cccc/guild.yml
    <exit 0>

The `--working` option diffs to the project directory.

    >>> run("guild diff --cmd echo --working")
    ???/.guild/runs/cccc .../diff-test-project/
    <exit 0>

    >>> run("guild diff --cmd echo bbbb --working")
    ???/runs/bbbb/.guild/sourcecode .../diff-test-project
    <exit 0>

`--working` implies `--sourcecode` - providing both is okay.

    >>> run("guild diff --cmd echo bbbb --working")
    ???/runs/bbbb/.guild/sourcecode .../diff-test-project
    <exit 0>

Source code to project subdir with `--dir` option:

    >>> run("guild diff --cmd echo --dir foobar")
    ???/.guild/runs/cccc foobar
    <exit 0>

Working with two run args is not allowed.

    >>> run("guild diff -c echo 1 2 --working")
    guild: cannot specify second RUN and --working
    <exit 1>

Dir with two run args is not allowed.

    >>> run("guild diff -c echo 1 2 --dir foobar")
    guild: cannot specify second RUN and --dir
    <exit 1>

## Other Paths

Output:

    >>> run("guild diff -c echo --output")
    ???/.guild/runs/bbbb/.guild/output .../.guild/runs/cccc/.guild/output
    <exit 0>

Env:

    >>> run("guild diff -c echo --env")
    ???/.guild/runs/bbbb/.guild/attrs/env .../.guild/runs/cccc/.guild/attrs/env
    <exit 0>

Flags:

    >>> run("guild diff -c echo --flags")
    ???/.guild/runs/bbbb/.guild/attrs/flags .../.guild/runs/cccc/.guild/attrs/flags
    <exit 0>

Attrs:

    >>> run("guild diff -c echo --attrs")
    ???/.guild/runs/bbbb/.guild/attrs .../.guild/runs/cccc/.guild/attrs
    <exit 0>

Deps:

    >>> run("guild diff -c echo --deps")
    ???/.guild/runs/bbbb/.guild/attrs/deps .../.guild/runs/cccc/.guild/attrs/deps
    <exit 0>

Multiple:

    >>> run("guild diff -c echo --deps --output -p foo -p bar --flags")
    ???/.guild/runs/bbbb/.guild/attrs/flags .../.guild/runs/cccc/.guild/attrs/flags
    .../.guild/runs/bbbb/.guild/attrs/deps .../.guild/runs/cccc/.guild/attrs/deps
    .../.guild/runs/bbbb/.guild/output .../.guild/runs/cccc/.guild/output
    .../.guild/runs/bbbb/foo .../.guild/runs/cccc/foo
    .../.guild/runs/bbbb/bar .../.guild/runs/cccc/bar
    <exit 0>

Duplicating attrs with other options:

    >>> run("guild diff -c echo --attrs --deps --flags --env")
    WARNING: ignoring --env (already included in --attrs)
    WARNING: ignoring --flags (already included in --attrs)
    WARNING: ignoring --deps (already included in --attrs)
    .../.guild/runs/bbbb/.guild/attrs .../.guild/runs/cccc/.guild/attrs
    <exit 0>


## Package Source Code Location

Guild uses the package location when working is specified for a
packaged operation.

Run a packaged operation.

    >>> run("guild run hello:default --run-id=dddd -y")
    Hello Guild!
    <exit 0>

Diff the run with `--working`.

    >>> run("guild diff -c echo --working")
    ???/.guild/runs/dddd/.guild/sourcecode .../site-packages/gpkg/hello/
    <exit 0>

## Incompatible Options

    >>> run("guild diff -c echo --dir foo --working")
    guild: --working and --dir cannot both be specified
    Try 'guild diff --help' for more information.
    <exit 1>
