# Numeric Run IDs

These tests settle are intended to settle once and for all time the
nagging problem of handling partial run IDs that look like numbers.

Run IDs are specified as flag values for required runs. If the
standard YAML decoder is used for run IDs, it's possible that the
value is converted to a number, which cannot be used to match run IDs.

Previous attempts to deal with this problem involve modifying the YAML
decoding rules to look for special numeric values that are possible
run IDs.

The current approach is to apply the simple heuristic that, when a
value is specified for a required operation, that value is a string
type. There is no need to anticipate the use of the value apart from
its op def context.

To test, we create a project that defines upstream and downstream
runs.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "guild.yml"), """
    ... upstream: guild.pass
    ...
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ...       warn-if-empty: no
    ... """)

    >>> cd(project_dir)

    >>> run("guild ops")
    ???downstream
    upstream
    <exit 0>

We use a separate Guild home to isolate runs.

    >>> gh = mkdtemp()

Create a helper function to run Guild commands in context of Guild home.

    >>> _run = run
    >>> def run(cmd):
    ...     if cmd.startswith("guild "):
    ...         cmd = "guild -H '%s' %s" % (gh, cmd[6:])
    ...     _run(cmd)

Generate upstream runs with run IDs that can be interpreted as number
values when specified entirely or in part.

    >>> runs_dir = path(gh, "runs")

    >>> quiet("guild run upstream --run-dir '%s/010' -y" % runs_dir)
    >>> quiet("guild run upstream --run-dir '%s/100' -y" % runs_dir)
    >>> quiet("guild run upstream --run-dir '%s/020abc' -y" % runs_dir)
    >>> quiet("guild run upstream --run-dir '%s/1e123' -y" % runs_dir)
    >>> quiet("guild run upstream --run-dir '%s/2e234abc' -y" % runs_dir)
    >>> quiet("guild run upstream --run-dir '%s/02e234abc' -y" % runs_dir)

    >>> run("guild runs")
    [1:02e234ab]  upstream  ...  completed
    [2:2e234abc]  upstream  ...  completed
    [3:1e123]     upstream  ...  completed
    [4:020abc]    upstream  ...  completed
    [5:100]       upstream  ...  completed
    [6:010]       upstream  ...  completed
    <exit 0>

Generate dowstream runs using various run ID references, each of which
is a YAML encoded number.

    >>> run("guild run downstream upstream=1 -y")
    ???Resolving upstream dependency
    Using run 1e123 for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=10 -y")
    Resolving upstream dependency
    Using run 100 for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=100 -y")
    Resolving upstream dependency
    Using run 100 for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=1e12 -y")
    Resolving upstream dependency
    Using run 1e123 for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=02 -y")
    Resolving upstream dependency
    Using run 02e234abc for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=2 -y")
    Resolving upstream dependency
    Using run 2e234abc for upstream resource
    <exit 0>

    >>> run("guild run downstream upstream=2e234 -y")
    Resolving upstream dependency
    Using run 2e234abc for upstream resource
    <exit 0>
