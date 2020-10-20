# Project API

The `_test` module provides a handy interface for working with a
project. While this is not yet released as a public API (as of 0.7) it
will likely at some point.

These tests exercise various project methods.

We'll use the 'simple' sample project for our tests.

    >>> project = Project(sample("projects", "simple"))

## Running an operation

The project API supports two methods of running an operation:

 - Run silently
 - Run without capturing anything
 - Run and capture a run object and the operation output

Run silently:

    >>> project.run_quiet("simple")

Run without capture:

    >>> project.run("simple")
    x: 1.0
    y: 2.0

Run with capture:

    >>> run, out = project.run_capture("simple")

    >>> run
    <guild.run.Run '...'>

    >>> print(out)
    x: 1.0
    y: 2.0

## Listing runs

The `list_runs()` method returns a list of runs associated with the
project.

    >>> runs = project.list_runs()

    >>> len(runs)
    3

 As with the CLI, runs are sorted from newest to oldest:

     >>> runs[0].id == run.id
     True

## Filtering runs

Runs can be listed using any of the available filters.

Let's generate a run with a label:

    >>> project.run_quiet("simple", label="hello")

And list runs matching that label:

    >>> runs = project.list_runs(labels=["hello"])

    >>> len(runs)
    1
    >>> runs[0].get("label")
    'hello'

And runs that are unlabeled:

    >>> len(project.list_runs(unlabeled=True))
    0

Runs for various time ranges:

    >>> len(project.list_runs(started="last 5 minutes"))
    4

    >>> len(project.list_runs(started="before 5 minutes ago"))
    0

Providing an supported filter generates an error:

    >>> project.list_runs(foo=123)
    Traceback (most recent call last):
    TypeError: runs_list() got an unexpected keyword argument 'foo'

Use a tag for a label.

    >>> project.run_quiet("simple", tags=["a_tag"])

    >>> runs = project.list_runs(labels=["a_tag"])

    >>> len(runs)
    1
    >>> runs[0].get("label")
    'a_tag x=1.0'

## Printing runs

The project API supports a simple function for printing runs.

By default, the function prints the operation name for all runs:

    >>> project.print_runs()
    simple
    simple
    simple
    simple
    simple

You can alternatively specify a list of runs:

    >>> runs = project.list_runs()
    >>> project.print_runs(runs[:2])
    simple
    simple

The function supports a list of options for including additional
column. Each may be used separately or in a group as needed.

    >>> project.print_runs(runs[:3], flags=True, labels=True, status=True)
    simple  x=1.0  a_tag x=1.0  completed
    simple  x=1.0  hello        completed
    simple  x=1.0  x=1.0        completed

## Deleting runs

Runs can be deleted using `delete_runs()`.

Let's delete the first run:

    >>> run = runs[-1]
    >>> exists(run.dir)
    True

    >>> project.delete_runs(runs=[run.id])
    Deleted 1 run(s)

    >>> exists(run.dir)
    False

We can also delete using filters.

    >>> project.delete_runs(labels=["hello"])
    Deleted 1 run(s)

    >>> project.print_runs(labels=True)
    simple  a_tag x=1.0
    simple  x=1.0
    simple  x=1.0

## Mark runs

Runs can be marked:

    >>> run = project.list_runs()[0]
    >>> print(run.get("marked"))
    None

    >>> project.mark(runs=[run.id])
    Marked 1 run(s)

    >>> run.get("marked")
    True

And unmarked:

    >>> project.mark(runs=[run.id], clear=True)
    Unmarked 1 run(s)

    >>> print(run.get("marked"))
    None

## Compare

Runs can be compared:

    >>> project.compare()
    [['run', 'operation', 'started', 'time', 'status', 'label', 'x', 'step', 'y'],
     ['...', 'simple', '...', '0:00:00', 'completed', 'x=1.0', 1.0, 0, 2.0],
     ['...', 'simple', '...', '0:00:00', 'completed', 'x=1.0', 1.0, 0, 2.0]]

With extra cols:

    >>> project.compare(extra_cols=True)
    [['run', 'operation', 'started', 'time', 'status', 'label', 'sourcecode', 'x', 'step', 'y'],
     ['...', 'simple', '...', '0:00:00', 'completed', 'x=1.0', 'fced27f4', 1.0, 0, 2.0],
     ['...', 'simple', '...', '0:00:00', 'completed', 'x=1.0', 'fced27f4', 1.0, 0, 2.0]]

## Other functions

The project API is used extensively throughout these tests. To avoid
duplicating time consuming tests, we will not include additional tests
here. Refer to those other tests for further examples.
