# Batch runs - fail on trial error

By default, a batch run continues to run remaining trials when a trial
run exits with an error.

    >>> project = Project(sample("projects", "batch"))

## Default batches

Use the `error.py` script to simluate trial errors.

    >>> project.run("error.py", flags={"fail": [True, False]})
    INFO: [guild] Running trial ...: error.py (fail=yes)
    FAIL
    ERROR: [guild] Trial ... exited with an error (1) - see log for details
    INFO: [guild] Running trial ...: error.py (fail=no)

Our runs:

    >>> project.print_runs(status=True)
    error.py   completed
    error.py   error
    error.py+  completed

Clear our runs:

    >>> project.delete_runs()
    Deleted 3 run(s)

    >>> project.print_runs()

If we specify `fail_on_trial_error`, the batch fails as soon as the
first trial error occurs.

    >>> project.run("error.py", flags={"fail": [True, False]}, fail_on_trial_error=True)
    INFO: [guild] Running trial ...: error.py (fail=yes)
    FAIL
    ERROR: [guild] Trial ... exited with an error (1) - see log for details
    ERROR: [guild] Stopping batch because a trial failed (remaining staged trials
    may be started as needed)
    <exit 1>

Our runs - note that the batch run has failed and that the second run
remains as staged.

    >>> project.print_runs(status=True)
    error.py   error
    error.py   staged
    error.py+  error

## Fail on trial error and steps

Stepped operations do not continue when a step fails. Note that a step
is not a trial and therefore this option is not applicable to steps.

Here's a Guild file with a steps op that runs an error script twice:

    >>> project = Project(mkdtemp())

    >>> write(path(project.cwd, "guild.yml"), """
    ... steps:
    ...   steps:
    ...     - error.py --label e1
    ...     - error.py --label e2
    ... """)

The error script:

    >>> write(path(project.cwd, "error.py"), """
    ... raise SystemExit("FAIL")
    ... """)

When we run steps, it fails after the first step.

    >>> project.run("steps")
    INFO: [guild] running error.py: error.py --label e1
    FAIL
    <exit 1>

    >>> project.print_runs(status=True, labels=True)
    error.py  e1  error
    steps         error

## Skopt based batches

Fail on error is supported by skopt based operation (sequential optimizers).

We use the `batch` sample project to illustrate.

    >>> project = Project(sample("projects", "batch"))

The default behavior is to keep running when an error occurs.

    >>> project.run("error.py", optimizer="forest", flags={"fail": [True]}, max_trials=2)
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: error.py (fail=yes)
    FAIL
    ERROR: [guild] Trial ... exited with an error (1) - see log for details
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: error.py (fail=yes)
    FAIL
    ERROR: [guild] Trial ... exited with an error (1) - see log for details

The optimization run stops on the first error when we specify fail on trial error.

    >>> project.run("error.py", optimizer="forest", flags={"fail": [True]}, max_trials=2,
    ...             fail_on_trial_error=True)
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: error.py (fail=yes)
    FAIL
    ERROR: [guild] Trial ... exited with an error (1) - see log for details
    ERROR: [guild] Stopping optimization run because a trial failed
    <exit 1>
