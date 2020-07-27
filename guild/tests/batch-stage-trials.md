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
    say.py   loud=no msg=c                                                completed
    say.py   loud=no msg=b                                                completed
    say.py   loud=no msg=a                                                completed
    queue    gpus=null poll-interval=10 run-once=yes wait-for-running=no  completed
    say.py+                                                               completed

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
    say.py+ staged as ...
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

## Stage trials via steps

If a stepped operation generates a batch and `--stage-trials` is
specified, the generated batch will stage the trials rather than run
them.

For our tests, we delete the current runs.

    >>> project.delete_runs()
    Deleted 4 run(s)

The `say-many` operation uses `steps` to run `say.py` in a batch.

First, the operation first without `--stage-trials`:

    >>> project.run("say-many")
    INFO: [guild] running say.py: say.py msg=[hi, hello, hola]
    INFO: [guild] Running trial ...: say.py (loud=no, msg=hi)
    hi
    INFO: [guild] Running trial ...: say.py (loud=no, msg=hello)
    hello
    INFO: [guild] Running trial ...: say.py (loud=no, msg=hola)
    hola

The runs are complete:

    >>> project.print_runs(status=True, labels=True)
    say.py    loud=no msg=hola   completed
    say.py    loud=no msg=hello  completed
    say.py    loud=no msg=hi     completed
    say.py+                      completed
    say-many                     completed

Next, use `--stage-trials`:

    >>> project.run("say-many", stage_trials=True)
    INFO: [guild] running say.py: say.py --stage-trials msg=[hi, hello, hola]
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=hi)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=hello)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    INFO: [guild] Staging trial ...: say.py (loud=no, msg=hola)
    say.py staged as ...
    To start the operation, use 'guild run --start ...'

And the runs:

    >>> project.print_runs(status=True, labels=True)
    say.py    loud=no msg=hola   staged
    say.py    loud=no msg=hello  staged
    say.py    loud=no msg=hi     staged
    say.py+                      completed
    say-many                     completed
    say.py    loud=no msg=hola   completed
    say.py    loud=no msg=hello  completed
    say.py    loud=no msg=hi     completed
    say.py+                      completed
    say-many                     completed
