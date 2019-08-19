# Scalars

The sample project `scalars` has an operation that illustrates scalar
generation for an run.

    >>> project = Project(sample("projects", "scalars"))

The operation `ouptut-and-summaries` uses both output scalars and
writes summaries using a summary writer.

    >>> project.run("output-and-summaries")
    min_loss: ...

    >>> runs = project.list_runs()
    >>> len(runs)
    1

    >>> run = runs[0]

Here are the tfevent files generated for the run:

    >>> [path for path in findl(run.dir) if "tfevent" in path]
    ['.guild/events.out.tfevents...',
     'events.out.tfevents...']

And the scalars:

    >>> scalars = [
    ...     {
    ...         "tag": s["tag"],
    ...         "prefix": s["prefix"],
    ...         "count": s["count"]
    ...     }
    ...     for s in project.scalars(run)
    ...     if s["tag"] in ("loss", "min_loss")
    ... ]

    >>> pprint(scalars)
    [{'count': 60, 'prefix': '', 'tag': 'loss'},
     {'count': 1, 'prefix': '.guild', 'tag': 'min_loss'}]
