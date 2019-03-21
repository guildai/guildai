# Marked runs

A marked run is used when resolving operation dependencies. If a
marked run does not exist for a required operation, the latst run for
that operation is used.

Runs are marked by users or by optimizers.

We'll illustrate using the `batch-deps` sample project.

    >>> project = Project(sample("projects", "batch-deps"))

In this project, the `serve` operation requires a `train` operation.

    >>> project.run("serve")
    Resolving train dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:train' in train resource: no suitable run for train
    <exit 1>

## Using the latest run for a required operation

We satisfy the dependency by running train:

    >>> project.run("train", flags={"lr": 0.1})
    params:
     lr=0.100000
    loss: ...
    Saving model as ./trained-model

And now serve again:

    >>> project.run("serve")
    Resolving train dependency
    Using output from run ... for train resource
    Serving ./trained-model

Let's take a moment to confirm that the dependency used matches the
run we expect.

Here are the current runs:

    >>> project.print_runs(flags=True, status=True)
    serve          completed
    train  lr=0.1  completed
    serve          error

Note the first run is `error` because it failed to resolve the
required dependency.

Here's a helper to get the run ID of the train dependency:

    >>> def train_dep(serve_run):
    ...     deps = serve_run.get("deps")
    ...     assert "train" in deps, deps
    ...     train_sources = deps["train"]
    ...     assert len(train_sources) == 1, deps
    ...     model_path = train_sources[0]
    ...     return os.path.basename(os.path.dirname(model_path))

Let's confirm that the run ID of the serve train dependency equals the
expected run.

    >>> runs = project.list_runs()
    >>> train_run = runs[1]
    >>> train_run.opref.to_opspec()
    'train'

    >>> serve_run = runs[0]
    >>> serve_run.opref.to_opspec()
    'serve'

    >>> train_dep(serve_run) == train_run.id
    True

Next we'll run train again, generating a more recent train op.

    >>> project.run("train", flags={"lr": 0.01})
    params:
     lr=0.010000
    loss: ...
    Saving model as ./trained-model

And run serve again:

    >>> project.run("serve")
    Resolving train dependency
    Using output from run ... for train resource
    Serving ./trained-model

Our runs:

    >>> project.print_runs(flags=True, status=True)
    serve           completed
    train  lr=0.01  completed
    serve           completed
    train  lr=0.1   completed
    serve           error

Let's confirm that the latest serve is using the latest train.

    >>> runs = project.list_runs()
    >>> train_run = runs[1]
    >>> train_run.opref.to_opspec()
    'train'

    >>> serve_run = runs[0]
    >>> serve_run.opref.to_opspec()
    'serve'

    >>> train_dep(serve_run) == train_run.id
    True

## Using an explicit run for a required operation

Next we explicitly specify a different train operation for serve:

    >>> explicit_train_run = runs[3]
    >>> train_run.opref.to_opspec()
    'train'
    >>> explicit_train_run.get("flags")
    {'lr': 0.1}

    >>> project.run("serve", flags={"train": explicit_train_run.id})
    Resolving train dependency
    Using output from run ... for train resource
    Serving ./trained-model

Let's confirm that the latest run is using the expected train run.

    >>> runs = project.list_runs()
    >>> serve_run = runs[0]
    >>> serve_run.opref.to_opspec()
    'serve'

    >>> train_dep(serve_run) == explicit_train_run.id
    True

## Marking a run for a required operation

Next, we'll mark a train run to indicate it should be used for
serve's train dependency.

    >>> project.mark(explicit_train_run.id)
    Marked 1 run(s)

Here are the marked runs:

    >>> project.print_runs(project.list_runs(marked=True), flags=True)
    train  lr=0.1

And the `marked` attribute:

    >>> explicit_train_run.get("marked")
    True

And run serve, this time without an explicit train run:

    >>> project.run("serve")
    Resolving train dependency
    Using output from run ... for train resource
    Serving ./trained-model

And confirm that the train dependency uses the marked run:

    >>> runs = project.list_runs()
    >>> serve_run = runs[0]
    >>> serve_run.opref.to_opspec()
    'serve'

    >>> train_dep(serve_run) == explicit_train_run.id
    True

## Unmarking and using latest again

Finally, we'll unmark the marked train run and verify that the next
serve run once again uses the latest trian run for its dependency.

    >>> project.mark(explicit_train_run.id, clear=True)
    Unmarked 1 run(s)

We no longer have marked runs:

    >>> project.print_runs(project.list_runs(marked=True))

And the `marked` attr:

    >>> print(explicit_train_run.get("marked"))
    None

Our runs:

    >>> project.print_runs(flags=True)
    serve
    serve
    serve
    train  lr=0.01
    serve
    train  lr=0.1
    serve

The latest train run:

    >>> latest_train_run = project.list_runs()[3]
    >>> latest_train_run.opref.to_opspec()
    'train'

Verify that the latest is not the explicit train run that we used
earlier:

    >>> latest_train_run.id != explicit_train_run.id
    True

Let's run the serve op:

    >>> project.run("serve")
    Resolving train dependency
    Using output from run ... for train resource
    Serving ./trained-model

And check our train dep:

    >>> runs = project.list_runs()
    >>> serve_run = runs[0]
    >>> serve_run.opref.to_opspec()
    'serve'

    >>> train_dep(serve_run) == latest_train_run.id
    True
