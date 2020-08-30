# Batch Handle Trial Status

A batch run must confirm that a trial is in a 'staged' state before
running it.

To illustrate, we work with the private API of `guild.batch_util`.

    >>> from guild import batch_util

Use a project to stage and test.

    >>> project = Project(mkdtemp(), guild_home=mkdtemp())

The runs dir for the project:

    >>> runs_dir = path(project.guild_home, "runs")

We use a simple script that prints an ID that can assign as a flag val.

    >>> write(path(project.cwd, "op.py"), "id = None")

Stage a batch:

    >>> project.run("op.py", optimizer="+", stage=True)
    op.py+ staged as ...
    To start the operation, use 'guild run --start ...

The current runs:

    >>> project.print_runs(status=True)
    op.py+  staged

We have a staged batch run that we can use to initialize some staged
trials.

    >>> batch_run = project.list_runs()[0]
    >>> batch_run.opref.to_opspec()
    '+'

Helper to init a trial run using `batch_util._init_trial_run`.

    >>> from guild import run as runlib

    >>> def init_trial_run(trial_flag_vals):
    ...     trial_run_id = runlib.mkid()
    ...     return batch_util.init_trial_run(
    ...         batch_run,
    ...         trial_flag_vals,
    ...         path(runs_dir, trial_run_id))


Initialize some trial runs.

    >>> trials = [{"id": 1}, {"id": 2}, {"id": 3}]
    >>> trial_runs = [init_trial_run(trial) for trial in trials]

Our runs:

    >>> project.print_runs(status=True, flags=True)
    op.py   id=3  staged
    op.py   id=2  staged
    op.py   id=1  staged
    op.py+        staged

    >>> trial_runs[0].get("flags")
    {'id': 1}

    >>> trial_runs[1].get("flags")
    {'id': 2}

    >>> trial_runs[2].get("flags")
    {'id': 3}

We want to run the trials to show how `batch_util` handles trial run
status. Here's a helper that uses `batch_util._try_run_staged` to
start a trial.

    >>> from guild import lock as locklib

    >>> def _run_trial(trial_run):
    ...     status_lock = locklib.Lock(locklib.RUN_STATUS, timeout=5)
    ...     with SetGuildHome(project.guild_home):
    ...         batch_util._try_run_staged_trial(trial_run, batch_run, status_lock)

Run the first staged trial.

    >>> with LogCapture() as logs:
    ...     _run_trial(trial_runs[0])

    >>> logs.print_all()
    Running trial ...: op.py (id=1)

Our runs:

    >>> project.print_runs(status=True, flags=True)
    op.py   id=1  completed
    op.py   id=3  staged
    op.py   id=2  staged
    op.py+        staged

If we run the first trial again, we Guild refuses because the trial is
not 'staged'.

    >>> trial_runs[0].status
    'completed'

    >>> with LogCapture() as logs:
    ...     _run_trial(trial_runs[0])

    >>> logs.print_all()
    WARNING: Skipping ... - status is 'completed' but expected 'staged'

Let's change the status of the second trial from 'staged' to 'pending'.

    >>> from guild import op_util

    >>> op_util.set_run_pending(trial_runs[1])

    >>> trial_runs[1].status
    'pending'

Try to start the second trial.

    >>> with LogCapture() as logs:
    ...     _run_trial(trial_runs[1])

    >>> logs.print_all()
    WARNING: Skipping ... - status is 'pending' but expected 'staged'

Finally, start the third trial.

    >>> with LogCapture() as logs:
    ...     _run_trial(trial_runs[2])

    >>> logs.print_all()
    Running trial ...: op.py (id=3)
