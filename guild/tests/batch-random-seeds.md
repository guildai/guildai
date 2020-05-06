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
    ...         max_trials=None, optimizer=None, **flags):
    ...     project.run(op, flags=flags,
    ...                 random_seed=random_seed,
    ...                 restart=restart,
    ...                 max_trials=max_trials,
    ...                 optimizer=optimizer)

    >>> def assert_random_seed(val):
    ...     assert isinstance(val, int), val
    ...     assert val >= 0 and val <= pow(2, 32), val

Let's run `echo.py` using its default values:

    >>> run("echo.py")
    1.0 2 'a'

Because we didn't explicitly provide a random seed for the operation,
the random seed for this run is generated at random.

    >>> rs = project.list_runs()[0].get("random_seed")
    >>> assert_random_seed(rs)

Let's run the same operation, but with an explicit random seed:

    >>> run("echo.py", random_seed=66)
    1.0 2 'a'

    >>> project.list_runs()[0].get("random_seed")
    66

In this case, `echo.py` doesn't make use of the random seed - but if
it did, the seed is available.

Delete the runs in preparation for the next tests.

    >>> project.delete_runs()
    Deleted 2 run(s)

## Batch operations and random seeds

When running a batch operation, any specified seed is used for the
batch, the batch proto, and all generated trials.

    >>> run("echo.py", x=[1, 2], random_seed=1)
    INFO: [guild] Running trial ...: echo.py (x=1, y=2, z=a)
    1 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2, y=2, z=a)
    2 2 'a'

The batch random seed:

    >>> batch = project.list_runs()[-1]
    >>> batch.get("random_seed")
    1

The proto random seed:

    >>> batch.batch_proto.get("random_seed")
    1

The trials random seed:

    >>> project.list_runs()[0].get("random_seed")
    1

    >>> project.list_runs()[1].get("random_seed")
    1

If we don't specify a random seed, a random seed is generated for both
the batch and the proto.

    >>> project.delete_runs()
    Deleted 3 run(s)

    >>> run("echo.py", x=[1, 2])
    INFO: [guild] Running trial ...: echo.py (x=1, y=2, z=a)
    1 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=2, y=2, z=a)
    2 2 'a'

The batch and proto seeds are different.

    >>> batch = project.list_runs()[-1]
    >>> batch_rs = batch.get("random_seed")

    >>> proto = batch.batch_proto
    >>> proto_rs = proto.get("random_seed")

    >>> batch_rs == proto_rs
    False
