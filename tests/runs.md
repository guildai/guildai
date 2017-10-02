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

## Run filters

We can filter runs by specifying a `filter` argument to the `runs`
function. A filter is a function that takes a run as a single argument
and returns True if the run should be returned or False if it should
not be returned.

Here we'll filter runs with an exist_status of "0" (i.e. run
successfully to completion):

    >>> [(run.short_id, run["exit_status"])
    ...  for run in runs(filter=lambda r: r.get("exit_status") == "0")]
    [('42803252', '0')]

`guild.var` provides a helper function that returns various named
filters:

- attr - true if a run attribute matches an expected value
- all - true if all filters are true
- any - true if any filters are true

Filter names may be preceded by '!' to negate them.

Here is the same filter as above, but using `run_filter`:

    >>> filter = guild.var.run_filter("attr", "exit_status", "0")
    >>> [(run.short_id, run["exit_status"]) for run in runs(filter=filter)]
    [('42803252', '0')]

Here's a list of runs with an exit_status not equals to "0":

    >>> filter = guild.var.run_filter("!attr", "exit_status", "0")
    >>> [(run.short_id, run.get("exit_status")) for run in runs(filter=filter)]
    [('360192fd', None), ('7d145216', '1')]

Runs with op equal to "mnist:evaluate" and exit_status equal to "0"
(i.e. successful evaluate operations):

    >>> filter = guild.var.run_filter(
    ...   "all",
    ...   [guild.var.run_filter("attr", "op", "mnist:evaluate"),
    ...    guild.var.run_filter("attr", "exit_status", "0")])
    >>> [(run.short_id, run.get("exit_status")) for run in runs(filter=filter)]
    [('42803252', '0')]

Runs with exit_status equal to "0" or "1":

    >>> filter = guild.var.run_filter(
    ...   "any",
    ...   [guild.var.run_filter("attr", "exit_status", "0"),
    ...    guild.var.run_filter("attr", "exit_status", "1")])
    >>> [(run.short_id, run.get("exit_status")) for run in runs(filter=filter)]
    [('42803252', '0'), ('7d145216', '1')]
