# Batch runs - skopt 3

These tests are a continuation of the skopt batch tests.

## Prev Trials Method

skopt based sequential optimizers (gp, forest, and gbrt) use previous
trials to suggest new hyperparameter values. The method used to get
previous sources is configurable using the `prev-trials` flag.

Previous trials can be used with one of these methods:

- `batch` - use only from the current optimization run (default)
- `sourcecode` - use any completed trial having the same source code
  as the current operation
- `operation` - use any completed trial having the same operation name
  regardless of its source code

We use an isolated Guild home for these tests.

    >>> set_guild_home(mkdtemp())

Use the Get Started train example.

    >>> cd(sample("projects/get-started"))

Start by generating some training runs.

    >>> quiet("guild run train.py x=-1.0 -y")
    >>> quiet("guild run train.py x=0.0 -y")
    >>> quiet("guild run train.py x=1.0 -y")

    >>> run("guild runs")
    [1:...]  train.py  ...  completed  noise=0.1 x=1.0
    [2:...]  train.py  ...  completed  noise=0.1 x=0.0
    [3:...]  train.py  ...  completed  noise=0.1 x=-1.0
    <exit 0>

### Batch Method

The default method to select previous trials is to limit trials to the
batch run.

Run each of the skopt sequential optimizers for a single trial and no
random starts. We use labels to delete the runs for cleanup.

    >>> run("guild run train.py x=[-1.0:1.0] -o gp -Fo random-starts=0 "
    ...     "-m 1 -l delme -bl delme -y")
    INFO: [guild] Random start for optimization (missing previous trials)
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o forest -Fo random-starts=0 "
    ...     "-m 1 -l delme -bl delme -y")
    INFO: [guild] Random start for optimization (missing previous trials)
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o gbrt -Fo random-starts=0 "
    ...     "-m 1 -l delme -bl delme -y")
    INFO: [guild] Random start for optimization (missing previous trials)
    ...
    <exit 0>

Note that each batch indicates that there are no previous trials.

Delete the runs in preparation for the next section.

    >>> run("guild runs rm -Fl delme -y")
    Deleted 6 run(s)
    <exit 0>

### Source Code Method

The 'sourcecode' method selects all runs with a matching source code digest.

    >>> run("guild run train.py x=[-1.0:1.0] -o gp -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o forest -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 4 previous trial(s) for use in optimization
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o gbrt -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 5 previous trial(s) for use in optimization
    ...
    <exit 0>

Delete the runs in preparation for the next section.

    >>> run("guild runs rm -Fl delme -y")
    Deleted 6 run(s)
    <exit 0>

### Operation Method

The 'operation' method selects all runs with a matching op spec even
if the source code changed. To test this mode, we create a new project
containing `train.py`.

    >>> cd(mkdtemp())

    >>> write("train.py", """
    ... x = 1.0
    ... print("loss: %f" % (x + 1))
    ... """)

Verify our three original runs.

    >>> run("guild runs")
    [1:...]  train.py  ...  completed  noise=0.1 x=1.0
    [2:...]  train.py  ...  completed  noise=0.1 x=0.0
    [3:...]  train.py  ...  completed  noise=0.1 x=-1.0
    <exit 0>

Verify that 'sourcecode' method does not see these runs.

    >>> run("guild run train.py x=[-1.0:1.0] -o gp -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y")
    ???INFO: [guild] Random start for optimization (missing previous trials)
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o forest -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o gbrt -Fo prev-trials=sourcecode "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 2 previous trial(s) for use in optimization
    ...
    <exit 0>

Delete these runs.

    >>> run("guild runs rm -Fl delme -y")
    Deleted 6 run(s)
    <exit 0>

Use 'operation' method. This uses the original runs as previous
trials, even though they use different source code.

    >>> run("guild run train.py x=[-1.0:1.0] -o gp -Fo prev-trials=operation "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o forest -Fo prev-trials=operation "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 4 previous trial(s) for use in optimization
    ...
    <exit 0>

    >>> run("guild run train.py x=[-1.0:1.0] -o gbrt -Fo prev-trials=operation "
    ...     "-Fo random-starts=0 -m 1 -l delme -bl delme -y",
    ...     ignore="The objective has been")
    INFO: [guild] Found 5 previous trial(s) for use in optimization
    ...
    <exit 0>

Delete runs from this section.

    >>> run("guild runs rm -Fl delme -y")
    Deleted 6 run(s)
    <exit 0>

## Errors

### Missing sourcecode digest

In the unlikely event that a batch proto does not have a source code
digest, the batch exits with an error.

To demonstrate, first stage one of the skopt batches to use source
code method to select previous trials.

    >>> run("guild run train.py x=[-1.0:1.0] -o gp -Fo prev-trials=sourcecode --stage -y")
    train.py+skopt:gp staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

To simulate a missing sourcecode digest, delete the proto run
'sourcecode_digest' attribute.

Get the batch run dir and ID.

    >>> batch_rundir, returncode = run_capture("guild select -p")
    >>> returncode
    0

    >>> batch_id, returncode = run_capture("guild select")
    >>> returncode
    0

Delete the proto sourcecode_digest attribute.

    >>> rmdir(path(batch_rundir, ".guild/proto/.guild/attrs/sourcecode_digest"))

Attempt to run the batch.

    >>> run("guild run --start %s -y" % batch_id)
    ERROR: [guild] Cannot find runs for batch proto in
    .../runs/.../.guild/proto: missing sourcecode digest
    <exit 1>
