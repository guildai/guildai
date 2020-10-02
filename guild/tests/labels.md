# Labels

    >>> project = Project(sample("projects", "optimizers"))

Generate a run.

    >>> project.run("echo.py")
    1.0 2 'a'

    >>> project.print_runs(labels=True)
    echo.py  x=1.0 y=2 z=a

Append 'a' to label.

    >>> project.label(append="a")
    Labeled 1 run(s)

    >>> project.print_runs(labels=True)
    echo.py  x=1.0 y=2 z=a a

Prepend 'b' to label.

    >>> project.label(prepend="b")
    Labeled 1 run(s)

    >>> project.print_runs(labels=True)
    echo.py  b x=1.0 y=2 z=a a

Remove 'b' from label.

    >>> project.label(remove="b")
    Labeled 1 run(s)

    >>> project.print_runs(labels=True)
    echo.py  x=1.0 y=2 z=a a

Set full label.

    >>> project.label(set="full label")
    Labeled 1 run(s)

    >>> project.print_runs(labels=True)
    echo.py  full label

Clear label.

    >>> project.label(clear=True)
    Cleared label for 1 run(s)

    >>> project.print_runs(labels=True)
    echo.py

Generate a run with tags.

    >>> project.run("echo.py", tags=["blue", "green"])
    1.0 2 'a'

    >>> project.print_runs(labels=True, limit=1)
    echo.py  blue green x=1.0 y=2 z=a

Generate a run with explicit label.

    >>> project.run("echo.py", label="third run")
    1.0 2 'a'

    >>> project.print_runs(labels=True, limit=1)
    echo.py  third run

Generate a run with tags and label.

    >>> project.run("echo.py", label="fourth run", tags=["yellow"])
    1.0 2 'a'

    >>> project.print_runs(labels=True, limit=1)
    echo.py  fourth run
