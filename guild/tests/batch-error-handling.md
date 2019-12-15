# Batch error handling

These tests illustrate how batches handle trial errors.

We use the `optimizers` sample project.

    >>> project = Project(sample("projects/optimizers"))

The script `trial_fail.py` simply exits with an error if its flag
`fail` is true.

The script `batch_fail.py` is an optimizer that runs an operation
setting the `fail` flag if the run index (one-based) is specified in
the optimizer `trials_fail` flag.

Let's run a batch, specifying that trials 2 and 3 should fail.

    >>> project.run(
    ...   "trial_fail.py",
    ...   optimizer="batch_fail.py",
    ...   max_trials=4,
    ...   opt_flags={"trials_fail": "2,3"},
    ...   label="trials")
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)
    INFO: [guild] Running trial ...: trial_fail.py (fail=yes)
    TRIAL FAIL
    INFO: [guild] Running trial ...: trial_fail.py (fail=yes)
    TRIAL FAIL
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)

Here are our runs:

    >>> project.print_runs(status=True, labels=True)
    trial_fail.py                trials           completed
    trial_fail.py                trials           error
    trial_fail.py                trials           error
    trial_fail.py                trials           completed
    trial_fail.py+batch_fail.py  batch_fail=no max_trials=5 trials_fail=2,3  completed

We can see that all 4 trials ran, with trials 2 and 3 failing.

The batch itself is `completed` because it ran to completion. The
status of individual trials does not effect batch status.

`batch_fail.py` can be made to fail by setting the `batch_fail` flag
to true. The batch whenever one of its trials fail `trials_fail`.

Let's cause the batch to fail at trial 2.

    >>> project.run(
    ...   "trial_fail.py",
    ...   optimizer="batch_fail.py",
    ...   max_trials=4,
    ...   opt_flags={
    ...     "trials_fail": "2",
    ...     "batch_fail": True},
    ...   label="batch")
    INFO: [guild] Running trial ...: trial_fail.py (fail=no)
    INFO: [guild] Running trial ...: trial_fail.py (fail=yes)
    TRIAL FAIL
    BATCH FAIL
    <exit 2>

And our runs:

    >>> project.print_runs(status=True, labels=True)
    trial_fail.py                batch                                        error
    trial_fail.py                batch                                        completed
    trial_fail.py+batch_fail.py  batch_fail=yes max_trials=5 trials_fail='2'  error
    trial_fail.py                trials                                       completed
    trial_fail.py                trials                                       error
    trial_fail.py                trials                                       error
    trial_fail.py                trials                                       completed
    trial_fail.py+batch_fail.py  batch_fail=no max_trials=5 trials_fail=2,3   completed
