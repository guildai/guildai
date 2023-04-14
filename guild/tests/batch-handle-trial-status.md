# Batch Handle Trial Status

A batch run confirms that a trial is in a 'staged' state before
running it.

To illustrate, we work with `guild.batch_util`.

    >>> from guild import batch_util

Use a simple script that prints an ID that can assign as a flag val.

    >>> guild_home = mkdtemp()
    >>> use_project(mkdtemp(), guild_home)

    >>> write("op.py", "id = None")

Stage an empty batch.

    >>> run("guild run op.py -o + --stage -y")
    op.py+ staged as ...
    To start the operation, use 'guild run --start ...

    >>> run("guild runs -s")
    [1]  op.py+  staged

We have a staged batch run that we can use to initialize some trials
using `init_trial_run` from `batch_util`.

    >>> from guild.batch_util import init_trial_run

Create a run for the batch that we can use with `init_trial_run`.

    >>> from guild import run as runlib

    >>> batch_run_dir = run_capture("guild select --dir")
    >>> batch_run = runlib.for_dir(batch_run_dir)

Initialize some trial runs.

    >>> trial_flags = [{"id": 1}, {"id": 2}, {"id": 3}]
    >>> trial_runs = [init_trial_run(batch_run, flags) for flags in trial_flags]

Guild generates three pending runs. Pending status indicates that the
runs are initialized and read to start by the batch parent run.

    >>> run("guild runs -s")
    [1]  op.py   pending  id=3
    [2]  op.py   pending  id=2
    [3]  op.py   pending  id=1
    [4]  op.py+  staged

Verify that each trial run is initialized with the expected flag
value.

    >>> trial_runs[0].get("flags")
    {'id': 1}

    >>> trial_runs[1].get("flags")
    {'id': 2}

    >>> trial_runs[2].get("flags")
    {'id': 3}

Guild confirms that each run status is `pending` before running it. If
Guild encounters a trial and a non-pending status, it skips the trial
and logs a message. Use the private `batch_util._start_pending_trial`
function to run a trial and check log output.

    >>> from guild.batch_util import _start_pending_trial

Create a helper to run `_start_staged_trial`.

    >>> def start_trial(trial_run):
    ...     from guild import lock
    ...     status_lock = lock.Lock(lock.RUN_STATUS, timeout=5)
    ...     with SetGuildHome(guild_home):
    ...         _start_pending_trial(trial_run, batch_run, status_lock)

Start the first trial.

    >>> with LogCapture() as logs:
    ...     start_trial(trial_runs[0])

Guild logs that it runs the trial.

    >>> logs.print_all()
    Running trial ...: op.py (id=1)

    >>> run("guild runs -s")
    [1]  op.py   completed  id=1
    [2]  op.py   pending    id=3
    [3]  op.py   pending    id=2
    [4]  op.py+  staged

Run the first trial again. Guild refuses because the trial status is
not `pending`.

    >>> with LogCapture() as logs:
    ...     start_trial(trial_runs[0])

    >>> logs.print_all()
    Skipping ... because its status is 'completed' (expected 'pending')

Change the status of the second trial from `pending` to
`staged`. First, confirm the current run status is `pending`.

    >>> trial_runs[1].status
    'pending'

Use `op_util` to set the status to staged.

    >>> from guild import op_util

    >>> op_util.set_run_staged(trial_runs[1])

    >>> trial_runs[1].status
    'staged'

Start the second trial. Guild skips it because it's status is staged
and not pending.

    >>> with LogCapture() as logs:
    ...     start_trial(trial_runs[1])

    >>> logs.print_all()
    Skipping ... because its status is 'staged' (expected 'pending')

Start the third trial.

    >>> with LogCapture() as logs:
    ...     start_trial(trial_runs[2])

    >>> logs.print_all()
    Running trial ...: op.py (id=3)

    >>> run("guild runs -s")
    [1]  op.py   completed  id=3
    [2]  op.py   staged     id=2
    [3]  op.py   completed  id=1
    [4]  op.py+  staged
