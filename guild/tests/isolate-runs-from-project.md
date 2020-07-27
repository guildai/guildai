# Isolate Runs from Project

These tests demonstrate that a run, staged or otherwise, is isolated
from its project and can be started or restarted even when the
original project is moved or deleted.

To illustrate, we use a sample project created in a temp location.

    >>> project = Project(mkdtemp())

Helper to print runs:

    >>> def print_runs():
    ...     project.print_runs(flags=True, status=True)

Write a Guild file that defines flags and requirements.

    >>> write(path(project.cwd, "guild.yml"), """
    ... op:
    ...   main: test
    ...   flags-import: all
    ...   flags:
    ...     a:
    ...       description: A
    ...     b:
    ...       description: B
    ...       default: 123
    ...   requires:
    ...     - file: a.txt
    ... """)

The other project files:

    >>> write(path(project.cwd, "test.py"), """
    ... from __future__ import print_function
    ... a = 1
    ... b = 2
    ... print(a, b)
    ... """)

    >>> write(path(project.cwd, "a.txt"), "hello")

Run `op`:

    >>> project.run("op")
    Resolving file:a.txt dependency
    1 123

Stage `op`:

    >>> project.run("op", stage=True, flags={"a": 2})
    Resolving file:a.txt dependency
    op staged as ...
    To start the operation, use ...

Our runs:

    >>> print_runs()
    op  a=2 b=123  staged
    op  a=1 b=123  completed

Delete the project files:

    >>> rm(path(project.cwd, "guild.yml"))
    >>> rm(path(project.cwd, "test.py"))
    >>> rm(path(project.cwd, "a.txt"))

Start the staged run. We can change flag values at this point.

    >>> runs = project.list_runs()
    >>> project.run(start=runs[0].id)
    Resolving file:a.txt dependency
    Skipping resolution of file:a.txt because it's already resolved
    2 123

    >>> print_runs()
    op  a=2 b=123  completed
    op  a=1 b=123  completed

Restart the initial run.

    >>> project.run(restart=runs[1].id)
    Resolving file:a.txt dependency
    Skipping resolution of file:a.txt because it's already resolved
    1 123

    >>> print_runs()
    op  a=1 b=123  completed
    op  a=2 b=123  completed

If we restar either run with different flag values, we get an
error. In this case, we need the Guild file.

    >>> project.run(restart=runs[0].id, flags={"a": 33, "b": 44})
    guild: cannot find definition for operation 'op' in run ...
    The definition is required when setting flags for start or restart.
    <exit 1>

    >>> project.run(restart=runs[1].id, flags={"a": "55", "b": True})
    guild: cannot find definition for operation 'op' in run ...
    The definition is required when setting flags for start or restart.
    <exit 1>

Runs have not changed.

    >>> print_runs()
    op  a=1 b=123  completed
    op  a=2 b=123  completed
