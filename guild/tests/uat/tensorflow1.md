# TensorFlow 1.x tests

These tests use `guild.tfevent`, which requires that we call
`ensure_tf_logging_patched` to supress TensorFlow logging noise.

    >>> guild.tfevent.ensure_tf_logging_patched()

Assert that we're starting with TensorFlow 1.x:

    >>> run("guild check")
    guild_version:             ...
    tensorflow_version:        1.14...
    ...
    tensorboard_version:       1.14...
    ...
    <exit 0>

We'll use the `tensorflow-vers` example project for our tests.

    >>> cd("examples/tensorflow-vers")

## Log system summaries with scalars

Run `summary1` op, which uses the TF 1.x API to log some scalars.

    >>> logdir = mkdtemp()
    >>> run("guild run -y summary1 logdir='%s'" % logdir,
    ...     ignore=["Refreshing", "is deprecated"])
    <exit 0>

Use `guild.tfevent.ScalarReader` to read the logged scalars:

    >>> sorted(guild.tfevent.ScalarReader(logdir))
    [...('sys/mem_free', ..., 1),
     ('sys/mem_total', ..., 1),
     ('sys/mem_used', ..., 1),
     ...
     ('x', 1.0, 1),
     ('x', 2.0, 2),
     ('x', 3.0, 3)]

## Behavior running TF 2.0 compatible script

When we run `summary2`, which uses the TF 2.0 summary API, we get an
error because TF 1.x doesn't support that interface:

    >>> run("guild run -y summary2 logdir=NOT-USED")
    INFO: [guild] Limiting traceback to user code. Use 'guild --debug
    run ...' for full stack.
    Traceback (most recent call last):
    ...
    AttributeError: ... has no attribute 'create_file_writer'
    <exit 1>
