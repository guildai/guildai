# Batch error handling

These tests illustrate how batches handle trial errors.

We use the `optimizers` sample project.

    >>> project = Project(sample("projects/optimizers"))

The script `trial_fail.py` simply exits with an error if its flag
`fail` is true.

The script `batch_fail.py` is an optimizer that runs an operation
setting the `fail` flag if the run zero-based index is specified in
the optimizer `trials_fail` flag.

Let's run a batch, specifying that trials 1 and 2 (zero based index)
should fail.

    >>> project.run(
    ...   "trial_fail.py",
    ...   optimizer="batch_fail.py",
    ...   max_trials=4,
    ...   opt_flags={"trials_fail": "1,2"},
    ...   label="trials")
    INFO: [guild] Initialized trial ... (fail=no)
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)
    INFO: [guild] Initialized trial ... (fail=yes)
    INFO: [guild] Running trial ...: trial_fail.py (fail=yes)
    TRIAL FAIL
    ERROR: [guild] Run ... failed - see logs for details
    INFO: [guild] Initialized trial ... (fail=yes)
    INFO: [guild] Running trial ...: trial_fail.py (fail=yes)
    TRIAL FAIL
    ERROR: [guild] Run ... failed - see logs for details
    INFO: [guild] Initialized trial ... (fail=no)
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)

Here are our runs:

    >>> project.print_runs(status=True, labels=True)
    trial_fail.py                trials  completed
    trial_fail.py                trials  error
    trial_fail.py                trials  error
    trial_fail.py                trials  completed
    trial_fail.py+batch_fail.py  trials  completed

We can see that all 4 trials ran, with trials 1 and 2 (zero based
index) failing.

The batch itself is `completed` because it ran to completion. The
status of individual trials does not effect batch status.

`batch_fail.py` can be made to fail by setting the `batch_fail` flag
to true. The batch will fail before the first trial specified in
`trials_fail`.

Let's cause the batch to fail just prior to trial 1 (zero based
index).

    >>> project.run(
    ...   "trial_fail.py",
    ...   optimizer="batch_fail.py",
    ...   max_trials=4,
    ...   opt_flags={
    ...     "trials_fail": "1",
    ...     "batch_fail": 1},
    ...   label="batch")
    INFO: [guild] Initialized trial ... (fail=no)
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)
    BATCH FAIL
    <exit 1>

And our runs:

    >>> project.print_runs(status=True, labels=True)
    trial_fail.py                batch   completed
    trial_fail.py+batch_fail.py  batch   error
    trial_fail.py                trials  completed
    trial_fail.py                trials  error
    trial_fail.py                trials  error
    trial_fail.py                trials  completed
    trial_fail.py+batch_fail.py  trials  completed
