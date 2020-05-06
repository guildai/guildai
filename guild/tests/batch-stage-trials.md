# Batch runs - stage trials

Batch trials can be staged using the `--stage-trials` option.

We use the `batch` project for these tests.

    >>> project = Project(sample("projects", "batch"))

Stage three trials:

    >>> project.run("say.py", flags={"msg": ["a", "b", "c"]}, stage_trials=True)
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=a)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=b)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=c)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'

The three trials are staged while the batch itself is completed.

    >>> project.print_runs(status=True, flags=True)
    say.py   loud=no msg=c  staged
    say.py   loud=no msg=b  staged
    say.py   loud=no msg=a  staged
    say.py+                 completed

Use a `queue` to run the staged trials.

    >>> project.run("queue", flags={"run-once": True})
    INFO: [queue] ... Processing staged runs
    INFO: [queue] ... Starting staged run ...
    a
    INFO: [queue] ... Starting staged run ...
    b
    INFO: [queue] ... Starting staged run ...
    c

Our runs after the queue finished.

    >>> project.print_runs(status=True, flags=True)
    say.py   loud=no msg=c                                              completed
    say.py   loud=no msg=b                                              completed
    say.py   loud=no msg=a                                              completed
    queue    gpus=null ignore-running=no poll-interval=10 run-once=yes  completed
    say.py+                                                             completed

## Staging batch runs that stage trials

We can, perhaps oddly, stage a batch operation that stages trials.

First clear our runs.

    >>> project.delete_runs()
    Deleted 5 run(s)

And stage a batch run that stages trials.

    >>> batch_run, out = project.run_capture(
    ...     "say.py", flags={"msg": ["a", "b", "c"]},
    ...     stage=True, stage_trials=True)

    >>> print(out)
    say.py+ staged in '...'
    To start the operation, use ...

NOTE: The instruction to start the operation using the run directory
is a result of using the project API, which specifies the --run-dir
CLI option to return a resulting run object.

Our runs:

    >>> project.print_runs(status=True)
    say.py+  staged

Let's start the staged run.

    >>> project.run(start=batch_run.id)
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=a)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=b)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=c)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'

And our runs:

    >>> project.print_runs(status=True, flags=True)
    say.py   loud=no msg=c  staged
    say.py   loud=no msg=b  staged
    say.py   loud=no msg=a  staged
    say.py+                 completed
