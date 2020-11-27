# Select Runs

A run can be selected using the `select` command or the `select()`
project method.

We use the `optimizers` project for our tests to generate runs with a
known loss.

    >>> project = Project(sample("projects", "optimizers"))

## Select API Function

Helper to test results:

    >>> def check(selected, runs, pos):
    ...     from guild import run as runlib
    ...     assert isinstance(selected, runlib.Run), selected
    ...     assert isinstance(runs[pos], runlib.Run), (runs, pos)
    ...     if selected.id != runs[pos].id:
    ...         print("error: expected %s but got %s" % (runs[pos].id, selected.id))
    ...         print("runs (%s):" % project.guild_home)
    ...         project.print_runs(runs, ids=True)

Generate three runs using the `range` flag function. Values for `f`
are used to calculate `loss. We specify USER env to test attribute
selection below.

    >>> with Env({"USER": "test"}):
    ...     project.run("echo2.py", flags={"f": "range[1.0:3.0]"})
    INFO: [guild] Running trial ...: echo2.py (b=yes, f=1.0, i=3, s=hello)
    i: 3
    f: 1.000000
    b: True
    s: hello
    loss: 0.000000
    INFO: [guild] Running trial ...: echo2.py (b=yes, f=2.0, i=3, s=hello)
    i: 3
    f: 2.000000
    b: True
    s: hello
    loss: 1.000000
    INFO: [guild] Running trial ...: echo2.py (b=yes, f=3.0, i=3, s=hello)
    i: 3
    f: 3.000000
    b: True
    s: hello
    loss: 2.000000

Get the runs for reference:

    >>> runs = project.list_runs()

    >>> len(runs)
    4

    >>> [_run.opref.op_name for _run in runs]
    ['echo2.py', 'echo2.py', 'echo2.py', '+']

By default, Guild selects the latest run:

    >>> check(project.select(), runs, 0)

Select run by position:

    >>> check(project.select("1"), runs, 0)

    >>> check(project.select("2"), runs, 1)

    >>> check(project.select("3"), runs, 2)

    >>> check(project.select("4"), runs, 3)

Select filtering by op:

    >>> check(project.select(ops=["+"]), runs, 3)

Select min loss:

    >>> check(project.select(min="loss"), runs, 2)

Select max loss:

    >>> check(project.select(max="loss"), runs, 0)

Select min of non-existing scalar - fails to alter sort order:

    >>> check(project.select(min="non-existing"), runs, 0)

No matching runs:

    >>> project.select("555555")
    Traceback (most recent call last):
    ValueError: ...

    >>> project.select(ops=["foo"])
    Traceback (most recent call last):
    ValueError: ...

    >>> project.select(terminated=True)
    Traceback (most recent call last):
    ValueError: ...

Invalid scalar spec:

    >>> project.select(min="foo bar")
    Traceback (most recent call last):
    ValueError: ("invalid scalar 'foo bar': unexpected token 'bar', line 1, pos 11", 1)

## Select Command

Full run ID (32 chars) are shown by default.

    >>> out, code = run_capture("guild select 1", guild_home=project.guild_home)
    >>> code, out
    (0, ...)
    >>> len(out.split("\n")[0])
    32

Use -s/--short-id to show only the short run ID.

    >>> out, code = run_capture("guild select 2 -s", guild_home=project.guild_home)
    >>> code, out
    (0, ...)
    >>> len(out.split("\n")[0]), out
    (8, ...)

Use -a/--attr to show a run attribute.

    >>> run("guild select 3 --attr run_dir", guild_home=project.guild_home)
    ???/runs/...
    <exit 0>

    >>> run("guild select 3 --attr status", guild_home=project.guild_home)
    completed
    <exit 0>

    >>> run("guild select 3 --attr label", guild_home=project.guild_home)
    b=yes f=1.0 i=3 s=hello
    <exit 0>

    >>> run("guild select 3 --attr user", guild_home=project.guild_home)
    test
    <exit 0>

An invalid attr generates an error.

    >>> run("guild select 3 --attr wombat", guild_home=project.guild_home)
    guild: no such run attribute 'wombat'
    <exit 1>
