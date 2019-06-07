# Batch runs - restarting

This test illustrates how a random optimized batch handles restarts.

Restarting a batch operation where trials can be pre-determined
follows this process:

- Trials are generated using the random seed from the previous run
  (i.e. the run being restarted). If that trial is already generated,
  it is not reinitialized. If it has not been generated, it is
  initialized for the first time. Guild determines "already generated"
  by the flag values for that run - if the flag values match, the
  trial is considered already generated and will not be
  re-initialized.

- The current generated trials list is stored as the batch `trials`
  run attr.

- Guild runs each newly generated trial. If a trial is orphaned -
  i.e. it no longer applies because it doesn't fall within the new
  trials - Guild deletes it only if it is pending. If the status is
  anything other than pending, it is left alone as an orphaned trial -
  i.e. it exits as an independent run that is not listed in the batch
  `trials` run attr.

- Guild always restarts a trial, even if it has been completed
  successfully. To skip completed trials, the user can specify the
  `--needed` option.

For our tests we work with the `optimizers` sample project:

    >>> project = Project(sample("projects", "optimizers"))

And some helpers:

    >>> def run(op=None, restart=None, init_trials=False,
    ...         print_trials=False, max_trials=None,
    ...         needed=True, **flags):
    ...     project.run(
    ...         op,
    ...         flags=flags,
    ...         restart=restart,
    ...         init_trials=init_trials,
    ...         print_trials=print_trials,
    ...         max_trials=max_trials,
    ...         simplify_trial_output=True)

    >>> def print_runs(runs=None, status=False):
    ...     project.print_runs(runs, flags=True, status=status)

We use Guild's built-in batch processing for grid search so we can
generate batch trials with consistent values.

As a baseline, let's run `echo.py` once using its default values:

    >>> run("echo.py")
    1.0 2 'a'

Our runs:

    >>> print_runs()
    echo.py x=1.0 y=2 z=a

For the rest of the tests, we look only at batches and restarts, so we
delete our runs before continuing.

    >>> project.delete_runs()
    Deleted 1 run(s)

    >>> print_runs()

## Initial batch run

For our initial batch run, we use two values each for flags `x` and
`y`:

    >>> run("echo.py", x=[1.0,2.0], y=[2,3])
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    Initialized trial (x=2.0, y=2, z=a)
    Running trial: echo.py (x=2.0, y=2, z=a)
    2.0 2 'a'
    Initialized trial (x=2.0, y=3, z=a)
    Running trial: echo.py (x=2.0, y=3, z=a)
    2.0 3 'a'

Let's get the run ID of the batch so we can restart it.

Here are the current runs:

    >>> runs_before_restart = project.list_runs()
    >>> print_runs(runs_before_restart)
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+

We see that the batch run the last.

    >>> batch_run = runs_before_restart[-1]
    >>> batch_run.opref.to_opspec()
    '+'

## Restarting without modification

Let's restart our batch run without modification:

    >>> run(restart=batch_run.id)
    Restarting ...
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    Initialized trial (x=2.0, y=2, z=a)
    Running trial: echo.py (x=2.0, y=2, z=a)
    2.0 2 'a'
    Initialized trial (x=2.0, y=3, z=a)
    Running trial: echo.py (x=2.0, y=3, z=a)
    2.0 3 'a'

When a batch run is restarted, its trials are restarted. Here are the
runs after the restart:

    >>> runs_after_restart = project.list_runs()
    >>> print_runs(runs_after_restart)
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+

Note this is the same output as the original run - we've only just
restarted everything. A batch restart does not generate new trials if
it doesn't need to. It will restart trials in-place.

Let's compare the trials before and after the restart:

    >>> run_ids_before = [_run.id for _run in runs_before_restart]
    >>> run_ids_after = [_run.id for _run in runs_after_restart]
    >>> run_ids_before == run_ids_after, (run_ids_before, run_ids_after)
    (True, ...)

## Restart with modified flags

When we restart a batch run using different flags, the batch generates
trials based on the new flag values. For each generated trial, it
looks for a matching trial from the previous run and restarts that run
in place. If it cannot find a matching run, it generates a new trial.

Let's first restart the batch with flags that generate a subset of the
original trials. In this case, we run with just one of the two
previous values of `x`:

    >>> run(restart=batch_run.id, x=1.0)
    Restarting ...
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'

Note that the previous values for `y` are used along with the new
single value for `x` to generate two trials.

Let's look at our runs:

    >>> print_runs()
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a

Note the two restarted runs appear at the top of the list, indicating
they are the most recently run.

Next we restart using without specifying any modified flags:

    >>> run(restart=batch_run.id)
    Restarting ...
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'

Note that the batch run is now associated with just two trials - it
remembers the flags used for the last restart run and uses those as
defaults for subsequent runs.

Next we run with flags that generate trials that include all of the
existing trials as well as some new trials.

    >>> run(restart=batch_run.id, x=1.0, y=[2,3,4])
    Restarting ...
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    Initialized trial (x=1.0, y=4, z=a)
    Running trial: echo.py (x=1.0, y=4, z=a)
    1.0 4 'a'

Here's our runs:

    >>> print_runs()
    echo.py   x=1.0 y=4 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a

Note now that there are five `echo.py` runs - the original four and
the new run generated by the latest restart.

## Restart with deleted trials

We can delete generated trials and they will be re-created as needed
when the batch is restarted.

Let's save our runs before deleting anything:

    >>> runs_before_delete = project.list_runs()

Let's delete two trials:

    >>> trials_to_delete = project.list_runs()[1:3]

    >>> print_runs(trials_to_delete)
    echo.py  x=1.0 y=3 z=a
    echo.py  x=1.0 y=2 z=a

    >>> project.delete_runs([_run.id for _run in trials_to_delete])
    Deleted 2 run(s)

And our runs:

    >>> print_runs()
    echo.py   x=1.0 y=4 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a

Let's now restart the batch:

    >>> run(restart=batch_run.id)
    Restarting ...
    Initialized trial (x=1.0, y=2, z=a)
    Running trial: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    Initialized trial (x=1.0, y=3, z=a)
    Running trial: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    Initialized trial (x=1.0, y=4, z=a)
    Running trial: echo.py (x=1.0, y=4, z=a)
    1.0 4 'a'

And our runs:

    >>> print_runs()
    echo.py   x=1.0 y=4 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a
    echo.py   x=2.0 y=2 z=a

Note the two deleted runs have been restored. However, they both have
new run IDs:

    >>> runs_after_restart = project.list_runs()

    >>> trials_to_delete[0].id in [_run.id for _run in runs_after_restart]
    False

    >>> trials_to_delete[1].id in [_run.id for _run in runs_after_restart]
    False

## Restarting individual trials

One of the benefits of Guild's approach to batches is that trials can
be restarted independenty of the batch that generated them.

To illustate, let's restart one of the earlier trials:

    >>> runs = project.list_runs()
    >>> trial_to_restart = runs[-1]
    >>> print_runs([trial_to_restart])
    echo.py  x=2.0 y=2 z=a

We first restart without flags:

    >>> run(restart=trial_to_restart.id)
    Restarting ...
    2.0 2 'a'

And our runs:

    >>> print_runs()
    echo.py   x=2.0 y=2 z=a
    echo.py   x=1.0 y=4 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a

Note that our restarted run is now listed first as it was most
recently run.

Next we restart the run with new flag values:

    >>> run(restart=trial_to_restart.id, x=3.0, y=5, z="b")
    Restarting ...
    3.0 5 'b'

And our runs:

    >>> print_runs()
    echo.py   x=3.0 y=5 z=b
    echo.py   x=1.0 y=4 z=a
    echo.py   x=1.0 y=3 z=a
    echo.py   x=1.0 y=2 z=a
    echo.py+
    echo.py   x=2.0 y=3 z=a

## Initializing trials

Guild supports init-only for trials. This generates the trial runs in
a `pending` state.

Let's first delete the current runs:

    >>> project.delete_runs()
    Deleted 6 run(s)

Let's generate four trials.

    >>> run("echo.py", x=[3.0,4.0], y=[5,6], z=["b","c"], init_trials=True)
    Initialized trial (x=3.0, y=5, z=b)
    Initialized trial (x=3.0, y=5, z=c)
    Initialized trial (x=3.0, y=6, z=b)
    Initialized trial (x=3.0, y=6, z=c)
    Initialized trial (x=4.0, y=5, z=b)
    Initialized trial (x=4.0, y=5, z=c)
    Initialized trial (x=4.0, y=6, z=b)
    Initialized trial (x=4.0, y=6, z=c)

Here are our runs with status:

    >>> print_runs(status=True)
    echo.py   x=4.0 y=6 z=c  pending
    echo.py   x=4.0 y=6 z=b  pending
    echo.py   x=4.0 y=5 z=c  pending
    echo.py   x=4.0 y=5 z=b  pending
    echo.py   x=3.0 y=6 z=c  pending
    echo.py   x=3.0 y=6 z=b  pending
    echo.py   x=3.0 y=5 z=c  pending
    echo.py   x=3.0 y=5 z=b  pending
    echo.py+                 pending

Note that all of the generated trials are in a `pending` state.

We can restart any of the trials to run it. Let's restart the first
generated trial:

    >>> trial_to_restart = project.list_runs()[-2]

    >>> print_runs([trial_to_restart])
    echo.py  x=3.0 y=5 z=b

Let's restart the trial:

    >>> run(restart=trial_to_restart.id)
    Restarting ...
    3.0 5 'b'

And our runs:

    >>> print_runs(status=True)
    echo.py   x=3.0 y=5 z=b  completed
    echo.py   x=4.0 y=6 z=c  pending
    echo.py   x=4.0 y=6 z=b  pending
    echo.py   x=4.0 y=5 z=c  pending
    echo.py   x=4.0 y=5 z=b  pending
    echo.py   x=3.0 y=6 z=c  pending
    echo.py   x=3.0 y=6 z=b  pending
    echo.py   x=3.0 y=5 z=c  pending
    echo.py+                 pending

Next we restart the entire batch:

    >>> batch_run = project.list_runs()[-1]

    >>> print_runs([batch_run])
    echo.py+

    >>> run(restart=batch_run.id)
    Restarting ...
    Initialized trial (x=3.0, y=5, z=b)
    Running trial: echo.py (x=3.0, y=5, z=b)
    3.0 5 'b'
    Initialized trial (x=3.0, y=5, z=c)
    Running trial: echo.py (x=3.0, y=5, z=c)
    3.0 5 'c'
    Initialized trial (x=3.0, y=6, z=b)
    Running trial: echo.py (x=3.0, y=6, z=b)
    3.0 6 'b'
    Initialized trial (x=3.0, y=6, z=c)
    Running trial: echo.py (x=3.0, y=6, z=c)
    3.0 6 'c'
    Initialized trial (x=4.0, y=5, z=b)
    Running trial: echo.py (x=4.0, y=5, z=b)
    4.0 5 'b'
    Initialized trial (x=4.0, y=5, z=c)
    Running trial: echo.py (x=4.0, y=5, z=c)
    4.0 5 'c'
    Initialized trial (x=4.0, y=6, z=b)
    Running trial: echo.py (x=4.0, y=6, z=b)
    4.0 6 'b'
    Initialized trial (x=4.0, y=6, z=c)
    Running trial: echo.py (x=4.0, y=6, z=c)
    4.0 6 'c'

    >>> print_runs(status=True)
    echo.py   x=4.0 y=6 z=c  completed
    echo.py   x=4.0 y=6 z=b  completed
    echo.py   x=4.0 y=5 z=c  completed
    echo.py   x=4.0 y=5 z=b  completed
    echo.py   x=3.0 y=6 z=c  completed
    echo.py   x=3.0 y=6 z=b  completed
    echo.py   x=3.0 y=5 z=c  completed
    echo.py   x=3.0 y=5 z=b  completed
    echo.py+                 completed

## Restarting a randomly generated batch

When restarting a batch that is generated through some random process,
the batch must consistently seed the process to ensure that the same
set of trials are generated given the same flags.

We'll look at two random batch operations in this test:

- Grid search with randomly selected max trials
- Random optimizer

Let's first delete any existing runs.

    >>> project.delete_runs()
    Deleted ... run(s)

    >>> print_runs()

### Grid search with max trials

A grid search randomly selects N max trials when max trials is less
than the number of generated trials.

Let's run a batch that would otherwise generate 6 trials, but with a
max trials of 4.

Here's the preview without max trials:

    >>> run("echo.py", x=[1,2,3], y=[5,4,6], z=["a","b","c"],
    ...     print_trials=True, max_trials=999)
    #   x  y  z
    1   1  5  a
    2   1  5  b
    3   1  5  c
    4   1  4  a
    5   1  4  b
    6   1  4  c
    7   1  6  a
    8   1  6  b
    9   1  6  c
    10  2  5  a
    11  2  5  b
    12  2  5  c
    13  2  4  a
    14  2  4  b
    15  2  4  c
    16  2  6  a
    17  2  6  b
    18  2  6  c
    19  3  5  a
    20  3  5  b
    21  3  5  c
    22  3  4  a
    23  3  4  b
    24  3  4  c
    25  3  6  a
    26  3  6  b
    27  3  6  c

Note this didn't generate any runs:

    >>> print_runs()

Let's run the batch, but with a max number of trials:

    >>> run("echo.py", x=[1, 2], y=[3, 4], z=["a", "b"], max_trials=4)
    Initialized trial ...
    Running trial: echo.py ...

Unfortunately we can't assert any set of values as the 4 are randomly
sampled from the 6. Even if we provided a random seed to the run
operation, the sampling will differ across versions of
Python. However, we can note the generated trials for comparison after
we restart the batch.

    >>> runs_before_restart = project.list_runs()
    >>> len(runs_before_restart)
    5

Let's restart the batch (the last run) and verify that the resulting
set of runs is the same as the original.

    >>> batch_run = runs_before_restart[-1]
    >>> batch_run.opref.to_opspec()
    '+'

    >>> run(restart=batch_run.id)
    Restarting ...

Here are the runs after the restart:

    >>> runs_after_restart = project.list_runs()
    >>> len(runs_after_restart)
    5

    >>> (([_run.id for _run in runs_before_restart] ==
    ...   [_run.id for _run in runs_after_restart]),
    ...  runs_before_restart,
    ...  runs_after_restart)
    (True, ...)
