# Runs

Runs are managed by the `var` module:

    >>> import guild.var

We can list runs using the `list_runs` function. By default
`list_runs` enumerates runs in the system location
(i.e. `~/.guild/runs`). For our tests we'll use the sample location.

Here's a helper function to list runs in that location:

    >>> def runs(**kw):
    ...     sample_runs = sample("runs")
    ...     return guild.var.runs(root=sample_runs, **kw)

By default runs are returned unsorted (based on how they're read from
the file system). We can can sort by various run attributes using the
`sort` argument. Here we order by id in reverse order:

    >>> [run.id for run in runs(sort=["-id"])]
    ['7d145216ae874020b735f001a7bfd27d',
     '42803252919c495cbd65f292f1f156a0',
     '360192fdf9b74f2fad5f514e9f2fdadb']

Sort by operation, then date:

    >>> [(run.short_id, run["op"], run["started"])
    ...  for run in runs(sort=["op", "started"])]
    [('42803252', 'mnist:evaluate', '1506790419'),
     ('360192fd', 'mnist:train', '1506790385'),
     ('7d145216', 'mnist:train', '1506790401')]

Sort by date, latest first:

    >>> [(run.short_id, run["started"])
    ...  for run in runs(sort=["-started"])]
    [('42803252', '1506790419'),
     ('7d145216', '1506790401'),
     ('360192fd', '1506790385')]

We can also filter runs. Here are runs that have an exit code of 0
(i.e. ran successfully to completion):

    >>> [(run.short_id, run["exit_status"])
    ...  for run in runs(filter=[("exit_status", "0")])]
    [('42803252', '0')]
