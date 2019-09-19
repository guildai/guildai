# Runs - part 2

This is a continuation of [Part 1](runs-1.md).

We continue examining the runs in samples/runs.

    >>> runs_dir = sample("runs")
    >>> guild_home = os.path.dirname(runs_dir)

We use gapi to for our tests:

    >>> from guild import _api as gapi
    >>> runs_list = lambda **kw: gapi.runs_list(guild_home=guild_home, **kw)

A helper to print runs:

    >>> def print_runs(runs):
    ...   for run in runs:
    ...     print(run.short_id, run.opref.to_opspec(), run.status)

Runs list:

    >>> print_runs(runs_list())
    42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Filtered by 'train' operation:

    >>> print_runs(runs_list(ops=["train"]))
    7d145216 mnist:train error
    360192fd mnist:train pending

Filtered by 'evaluate' operation:

    >>> print_runs(runs_list(ops=["evaluate"]))
    42803252 mnist:evaluate completed

Filtered by completed various status:

    >>> print_runs(runs_list(completed=True))
    42803252 mnist:evaluate completed

    >>> print_runs(runs_list(error=True))
    7d145216 mnist:train error

    >>> print_runs(runs_list(pending=True))
    360192fd mnist:train pending

    >>> print_runs(runs_list(pending=True, error=True))
    7d145216 mnist:train error
    360192fd mnist:train pending

    >>> runs_list(foobar=True)
    Traceback (most recent call last):
    TypeError: runs_list() got an unexpected keyword argument 'foobar'
