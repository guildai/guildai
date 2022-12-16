# Marked runs

A marked run is used when resolving operation dependencies. If a
marked run does not exist for a required operation, the latst run for
that operation is used.

Runs are marked by users or by optimizers.

We'll illustrate using the `batch-deps` sample project.

    >>> use_project("batch-deps")

In this project, the `serve` operation requires a `train` operation.

    >>> run("guild run serve -y")
    WARNING: cannot find a suitable run for required resource 'operation:train'
    Resolving operation:train
    guild: run failed because a dependency was not met: could not resolve
    'operation:train' in operation:train resource: no suitable run for train
    <exit 1>

## Using the latest run for a required operation

We satisfy the dependency by running train:

    >>> run("guild run train lr=0.1 -y")
    params:
     lr=0.100000
    loss: ...
    Saving model as ./trained-model

And now serve again:

    >>> run("guild run serve -y")
    Resolving operation:train
    Using run ... for operation:train
    Serving ./trained-model

Let's confirm that the dependency used matches the run we expect.

Here are our runs:

    >>> run("guild runs -s")
    [1]  serve  completed  model=...
    [2]  train  completed  lr=0.1
    [3]  serve  error      model=

Note that the original run is `error` because it failed to resolve the
required dependency.

A helper function to check that the resolved run is what we expect.

    >>> def assert_resolved_run(expected_select):
    ...     deps = yaml.safe_load(run_capture("guild select --attr deps"))
    ...     resolved_run_id = deps["operation:train"]["operation:train"]["config"]
    ...     expected_run_id = run_capture(f"guild select {expected_select}")
    ...     resolved_run_id == expected_run_id, (
    ...         "expected {expected_run_id} but got {resolved_run_id}"
    ...     )

Verify that the latest run resolved using the successful `train` run.

    >>> assert_resolved_run("-Sc -Fo train")

Next we'll run train again, generating a more recent train op.

    >>> run("guild run train lr=0.01 -y")
    params:
     lr=0.010000
    loss: ...
    Saving model as ./trained-model

And run serve again:

    >>> run("guild run serve -y")
    Resolving operation:train
    Using run ... for operation:train
    Serving ./trained-model

Our runs:

    >>> run("guild runs -s")
    [1]  serve  completed  model=...
    [2]  train  completed  lr=0.01
    [3]  serve  completed  model=...
    [4]  train  completed  lr=0.1
    [5]  serve  error      model=

Let's confirm that the latest serve is using the latest train.

    >>> assert_resolved_run("-Fo train -F lr=0.01")

## Using an explicit run for a required operation

Next we explicitly specify a different train operation for serve.

    >>> first_train_run = run_capture("guild select -Fo train 2")

Confirm that this is the expected run, where `lr` is `0.1`.

    >>> run(f"guild select --attr flags {first_train_run}")
    lr: 0.1

Specify the run ID for a new `serve` run:

    >>> run(f"guild run serve train={first_train_run} -y")
    Resolving operation:train
    Using run ... for operation:train
    Serving ./trained-model

Verify that the resolved run is as expected.

    >>> assert_resolved_run(first_train_run)

## Marking a run for a required operation

Guild uses marked runs by default when resolving for operation
dependencies.

Let's mark the first `train` run.

    >>> run(f"guild mark {first_train_run} -y")
    Marked 1 run(s)

    >>> run("guild runs -s")
    [1]  serve           completed  model=...
    [2]  serve           completed  model=...
    [3]  train           completed  lr=0.01
    [4]  serve           completed  model=...
    [5]  train [marked]  completed  lr=0.1
    [6]  serve           error      model=

When we run `serve` without specifying a `train` run, it uses the
marked run.

    >>> run("guild run serve -y")
    Resolving operation:train
    Using run ... for operation:train
    Serving ./trained-model

    >>> assert_resolved_run(first_train_run)

Let's unmark the first `train` run.

    >>> run(f"guild mark --clear {first_train_run} -y")
    Unmarked 1 run(s)

    >>> run("guild runs -s")
    [1]  serve  completed  model=...
    [2]  serve  completed  model=...
    [3]  serve  completed  model=...
    [4]  train  completed  lr=0.01
    [5]  serve  completed  model=...
    [6]  train  completed  lr=0.1
    [7]  serve  error      model=

When we run `serve` again, without an explicit `train` run, Guild uses
the latest `train` run by default.

    >>> run("guild run serve -y")
    Resolving operation:train
    Using run ... for operation:train
    Serving ./trained-model

The first train run is not resolved.

    >>> assert_resolved_run(first_train_run)

The latest train run is, however.

    >>> assert_resolved_run("-Fo train")
