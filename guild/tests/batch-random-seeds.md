# Batch runs - random seeds

Random seeds play an important role in supporting consistent behavior
for operations that use random sampling. Not all operations use random
sampling, but those that do need an unambiuous random seed that they
can use to generate consistent results.

For our tests, we'll use the `echo.py` script in the `optimizers`
project.

    >>> project = Project(sample("projects", "optimizers"))

Some helper functions:

    >>> def run(op=None, restart=None, random_seed=None,
    ...         max_trials=None, init_trials=False,
    ...         optimizer=None, **flags):
    ...     project.run(op, flags=flags,
    ...                 random_seed=random_seed,
    ...                 restart=restart,
    ...                 max_trials=max_trials,
    ...                 init_trials=init_trials,
    ...                 optimizer=optimizer,
    ...                 simplify_trial_output=True)

    >>> def random_seed(run=None):
    ...     run = run or project.list_runs()[0]
    ...     return run.get("random_seed")

    >>> def proto_random_seed(batch_run):
    ...     import guild.run
    ...     proto_run = guild.run.Run("", batch_run.guild_path("proto"))
    ...     return proto_run.get("random_seed")

    >>> def assert_random_seed(val):
    ...     assert isinstance(val, int), val
    ...     assert val >= 0 and val <= pow(2, 32), val

Let's run `echo.py` using its default values:

    >>> run("echo.py")
    1.0 2 'a'

Because we didn't explicitly provide a random seed for the operation,
the random seed for this run is generated at random.

    >>> rs = random_seed()
    >>> assert_random_seed(rs)

Let's now run the same operation, but with an explicit random seed:

    >>> run("echo.py", random_seed=66)
    1.0 2 'a'

    >>> random_seed()
    66

In this case, `echo.py` doesn't make use of the random seed - but if
it did, the seed is available.

Let's delete these runs in preparation for our next tests.

    >>> project.delete_runs()
    Deleted 2 run(s)

## Batch operations and random seeds

All batch operations use random sampling to limit the number of
generated trials to a specified maximum. In this case, the random seed
is used on both initial trial generation as well as any subsequent
trial generation. The random seed must not change during the lifetime
of a run to ensure consistent behavior.

Let's illustrate with a grid search of one run:

    >>> run("echo.py", x=[1])
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'

This generates two runs:

    >>> project.print_runs()
    echo.py
    echo.py+

As with the previous test, when we don't specify a random seed, one is
generated for us. There are three random seeds associated with the two
runs:

- Random seed associated with the batch run
- Random seed associated with the batch proto
- Random seed associated with the generated trial

Let's look at each of these.

    >>> batch_run = project.list_runs()[1]
    >>> batch_run_rs = random_seed(batch_run)
    >>> assert_random_seed(batch_run_rs)

    >>> batch_proto_rs = proto_random_seed(batch_run)
    >>> assert_random_seed(batch_proto_rs)

    >>> trial_run = project.list_runs()[0]
    >>> trial_run_rs = random_seed(trial_run)
    >>> assert_random_seed(trial_run_rs)

Batch and proto random seeds are always the same:

    >>> batch_run_rs == batch_proto_rs
    True

Trial run random seeds are always the same as the batch proto random
seed:

    >>> batch_proto_rs == trial_run_rs
    True

However, if we specify a seed explicitly, that value is used for the
batch, its proto, and all generated trials:

    >>> run("echo.py", x=[1], random_seed=77)
    Initialized trial (x=1, y=2, z=a)
    Running trial: echo.py (x=1, y=2, z=a)
    1 2 'a'

    >>> batch_run = project.list_runs()[1]
    >>> random_seed(batch_run)
    77

    >>> proto_random_seed(batch_run)
    77

    >>> trial_run = project.list_runs()[0]
    >>> random_seed(trial_run)
    77

Let's clear our runs for the next test.

    >>> project.delete_runs()
    Deleted 4 run(s)

## Random seeds and batch restarts

The random seed plays an important role in restarting batches. The
original random seed must be used when generating trials on a restart,
otherwise the list of generated trials won't match the first list for
the given set of batch flags.

### Example - random sampling of grid search

We illustrate by initializing trials of a large batch operation (100
trials) limited to 5 trials via a max trials option. Note that in this
case we do not specify a random seed.

    >>> run("echo.py", x=[1,2,3,4,5], y=[1,2,3,4,5], z=["a","b","c"],
    ...     init_trials=True, max_trials=5)
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...

Here are the generated trials:

    >>> project.print_runs(status=True)
    echo.py   pending
    echo.py   pending
    echo.py   pending
    echo.py   pending
    echo.py   pending
    echo.py+  pending

Let's note both the run ID and the flags hash for each of these
runs. We'll use these for comparison later.

    >>> from guild.op_util import flags_hash

    >>> trials_before_restart = [
    ...     (_run.id, flags_hash(_run.get("flags")))
    ...     for _run in project.list_runs()]

Next we'll restart the batch. Note again, we do not specify a random
seed, or any other parameter for that matter. The batch reuses the
settings from the original run.

    >>> batch_run = project.list_runs()[-1]

    >>> run(restart=batch_run.id)
    Restarting ...
    Initialized trial ...
    Running trial: echo.py ...
    Initialized trial ...
    Running trial: echo.py ...
    Initialized trial ...
    Running trial: echo.py ...
    Initialized trial ...
    Running trial: echo.py ...
    Initialized trial ...
    Running trial: echo.py ...

Here are the runs after the restart:

    >>> project.print_runs(status=True)
    echo.py   completed
    echo.py   completed
    echo.py   completed
    echo.py   completed
    echo.py   completed
    echo.py+  completed

Let's again generate a list of run IDs and flags hash:

    >>> trials_after_restart = [
    ...     (_run.id, flags_hash(_run.get("flags")))
    ...     for _run in project.list_runs()]

Because we sampled only 5 runs from 100, the random seed used in the
sampling process must be the same for the two lists - before restart
and after restart - to be the same.

    >>> (trials_before_restart == trials_after_restart,
    ...  trials_before_restart, trials_after_restart)
    (True, ...)

### Example - randomly generated trials

Let's run the same test using the random optimizer, which generates
random trials within a search space.

First we delete existing runs:

    >>> project.delete_runs()
    Deleted 6 run(s)

Let's initialize 5 trials randomly using a large search space for
`x`:

    >>> run("echo.py", optimizer="random",
    ...     x="[1:10000000]", max_trials=5,
    ...     init_trials=True)
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...
    Initialized trial ...

    >>> runs = project.list_runs()
    >>> len(runs)
    6

The trials before restarting:

    >>> trials_before_restart = [
    ...     (_run.id, flags_hash(_run.get("flags")))
    ...     for _run in runs]

Restart the batch:

    >>> batch_run = runs[-1]
    >>> run(restart=batch_run.id)
    Restarting ...

Runs after restart:

    >>> runs = project.list_runs()
    >>> len(runs)
    6

Trials with run IDs and flags hash after restart:

    >>> trials_after_restart = [
    ...     (_run.id, flags_hash(_run.get("flags")))
    ...     for _run in runs]

The trials before and after are equivalent for the same reason as
before: the batch operation used the same random seed when generating
trials.

    >>> trials_before_restart == trials_after_restart
    True
