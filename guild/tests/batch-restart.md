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

For our tests we'll use a temporary workspace:

    >>> workspace = mkdtemp()

We'll work with the `echo.py` script in the `optimizers` sample
project:

    >>> project = sample("projects", "optimizers")

We'll use Guild's built-in batch processing for grid search so we can
generate batch trials with consistent values.

Here's a helper to run ops:

    >>> def run(op, **flags):
    ...     from guild import _api as gapi
    ...     out = gapi.run_capture_output(
    ...         op,
    ...         flags=flags,
    ...         cwd=project,
    ...         guild_home=workspace)
    ...     print(out.strip())

A helper to list runs:

    >>> def list_runs():
    ...     return gapi.runs_list(guild_home=workspace)

A helper to print runs:

    >>> def print_runs(runs):
    ...     from guild import op_util
    ...     with Chdir(project):
    ...         for run in runs:
    ...             op_desc = op_util.format_op_desc(run)
    ...             flags_desc = " ".join(
    ...                 ["%s=%s" % (name, op_util.format_flag_val(val))
    ...                  for name, val in sorted(run.get("flags").items())])
    ...             print("[%s] %s %s" % (run.short_id, op_desc, flags_desc))

And a helper for deleting runs:

    >>> def delete_runs(runs=None):
    ...     from guild import _api as gapi
    ...     gapi.runs_delete(runs, guild_home=workspace)

As a baseline, let's run `echo.py` once using its default values:

    >>> run("echo.py")
    1.0 2 'a'

Our runs:

    >>> print_runs(list_runs())
    [...] echo.py x=1.0 y=2 z=a

Next we'll run a batch of four using flag lists.

    >>> run("echo.py", x=[1.0, 2.0], y=[2, 3])
    INFO: [guild] Initialed trial ... (x=1.0, y=2, z=a)
    INFO: [guild] Initialed trial ... (x=1.0, y=3, z=a)
    INFO: [guild] Initialed trial ... (x=2.0, y=2, z=a)
    INFO: [guild] Initialed trial ... (x=2.0, y=3, z=a)
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=1.0, y=3, z=a)
    1.0 3 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=2, z=a)
    2.0 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2.0, y=3, z=a)
    2.0 3 'a'

TODO (in no particular order):

- Restart a batch after a successful run
- Restart with some new args
- Run a random batch with a restart to show the same trials are
  generated given the same flags
- Restart individual trials
- Init only + restart
- Init only + restart of individual trials
- Restart after deleting a trial
