# Tags

    >>> project = Project(sample("projects", "optimizers"))

Generate runs with tags.

    >>> run1, out = project.run_capture("echo.py", tags=["foo"])
    >>> print(out)
    1.0 2 'a'

    >>> print(run1.get("tags"))
    ['foo']

    >>> run2, _ = project.run_capture("echo.py", tags=["bar"])
    >>> print(run2.get("tags"))
    ['bar']

    >>> run3, _ = project.run_capture("echo.py", tags=["baz", "bam"])
    >>> print(run3.get("tags"))
    ['baz', 'bam']

Show all runs.

    >>> project.print_runs(labels=True)
    echo.py  baz bam x=1.0 y=2 z=a
    echo.py  bar x=1.0 y=2 z=a
    echo.py  foo x=1.0 y=2 z=a

Show runs with tag 'foo'.

    >>> project.print_runs(project.list_runs(tags=["foo"]), labels=True)
    echo.py  foo x=1.0 y=2 z=a

Show runs with tag 'bam'.

    >>> project.print_runs(project.list_runs(tags=["foo", "bam"]), labels=True)
    echo.py  baz bam x=1.0 y=2 z=a
    echo.py  foo x=1.0 y=2 z=a

Remove 'bam' from latest run.

    >>> project.tag([run3.id], remove="bam", sync_labels=True)
    Modified tags for 1 run(s)

    >>> run3.get("tags")
    ['baz']

    >>> project.print_runs([run3], labels=True)
    echo.py  baz x=1.0 y=2 z=a

    >>> project.list_runs(tags=["bam"])
    []

Add tags 'abc' and 'def' to runs 1 and 2.

    >>> project.tag([run1, run2], add=["abc", "def"], sync_labels=True)
    Modified tags for 2 run(s)

    >>> run1.get("tags")
    ['abc', 'def', 'foo']

    >>> run2.get("tags")
    ['abc', 'bar', 'def']

    >>> project.print_runs([run1, run2], labels=True)
    echo.py  abc def foo x=1.0 y=2 z=a
    echo.py  abc def bar x=1.0 y=2 z=a

    >>> project.print_runs(project.list_runs(tags=["abc"]), labels=True)
    echo.py  abc def bar x=1.0 y=2 z=a
    echo.py  abc def foo x=1.0 y=2 z=a


Clear tags for run2.

    >>> project.tag([run2], clear=True, sync_labels=True)
    Modified tags for 1 run(s)

    >>> run2.get("tags")
    []

    >>> project.print_runs([run2], labels=True)
    echo.py  x=1.0 y=2 z=a

Clear and add tags to run3.

    >>> project.tag([run3], clear=True, add=["blue", "green"], sync_labels=True)
    Modified tags for 1 run(s)

    >>> run3.get("tags")
    ['blue', 'green']

    >>> project.print_runs([run3], labels=True)
    echo.py  blue green x=1.0 y=2 z=a

Clear tags from run3 without syncing labels.

    >>> project.tag([run3], clear=True)
    Modified tags for 1 run(s)

    >>> run3.get("tags")
    []

    >>> project.print_runs([run3], labels=True)
    echo.py  blue green x=1.0 y=2 z=a
