# Numeric Run IDs

These tests settle once and for all the nagging problem of handling
partial run IDs that look like numbers.

Run IDs are specified as flag values for required runs. If the
standard YAML decoder is used for run IDs, it's possible that the
value is converted to a number, which cannot be used to match run IDs.

Previous attempts to deal with this problem involve modifying the YAML
decoding rules to look for special numeric values that are possible
run IDs.

The current approach applies the heuristic that, when a value is
specified for a required operation, that value is a string type. There
is no need to anticipate the use of the value apart from its op def
context.

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

We use the project in an isolated Guild home.

    >>> gh = mkdtemp()
    >>> use_project(project_dir, gh)

Here are the project ops:

    >>> run("guild ops")
    downstream
    upstream
    <exit 0>

We generate upstream runs with run IDs that can be interpreted as
number values when specified entirely or in part.

    >>> runs_dir = path(gh, "runs")

    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/010' -y")
    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/100' -y")
    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/020abc' -y")
    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/1e123' -y")
    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/2e234abc' -y")
    >>> quiet(f"guild run upstream --run-dir '{runs_dir}/02e234abc' -y")

    >>> run("guild runs")
    [1:02e234ab]  upstream  ...  completed
    [2:2e234abc]  upstream  ...  completed
    [3:1e123]     upstream  ...  completed
    [4:020abc]    upstream  ...  completed
    [5:100]       upstream  ...  completed
    [6:010]       upstream  ...  completed

Generate dowstream runs using various run ID references, each of which
is a YAML encoded number.

    >>> run("guild run downstream upstream=1 -y")
    Resolving operation:upstream
    Using run 1e123 for operation:upstream

    >>> run("guild run downstream upstream=10 -y")
    Resolving operation:upstream
    Using run 100 for operation:upstream

    >>> run("guild run downstream upstream=100 -y")
    Resolving operation:upstream
    Using run 100 for operation:upstream

    >>> run("guild run downstream upstream=1e12 -y")
    Resolving operation:upstream
    Using run 1e123 for operation:upstream

    >>> run("guild run downstream upstream=02 -y")
    Resolving operation:upstream
    Using run 02e234abc for operation:upstream

    >>> run("guild run downstream upstream=2 -y")
    Resolving operation:upstream
    Using run 2e234abc for operation:upstream

    >>> run("guild run downstream upstream=2e234 -y")
    Resolving operation:upstream
    Using run 2e234abc for operation:upstream
