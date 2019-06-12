# TensorFlow 2.0

These tests use `guild.tfevent`, which requires that we call
`ensure_tf_logging_patched` to supress TensorFlow logging noise.

    >>> guild.tfevent.ensure_tf_logging_patched()

Install the latest pre-release version of 2.0 or greater):

    >>> run("pip install tensorflow>=2.0 --upgrade --pre")
    <BLANKLINE>
    <exit 0>

NOTE: This command changes the UAT runtime to use a new version of
TensorFlow. The version does not support GPU.

Check:

    >>> run("guild check")
    guild_version:             ...
    tensorflow_version:        2.0.0-beta0
    tensorflow_cuda_support:   no
    tensorflow_gpu_available:  no
    tensorboard_version:       1.14.0a20190603
    ...
    <exit 0>

We'll use the `tensorflow-vers` example project for our tests.

    >>> cd("examples/tensorflow-vers")

## Log system summaries with scalars

Run `summary2` op, which uses the TF 2.x API to log some scalars.

    >>> logdir = mkdtemp()
    >>> run("guild run -y summary2 logdir='%s'" % logdir,
    ...     ignore="I tensorflow/")
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

## Behavior running TF 1.0 compatible script

When we run `summary1`, which uses the TF 1.0 summary API, we get an
error because TF 1.x doesn't support that interface:

    >>> run("guild run -y summary1 logdir=NOT-USED")
    INFO: [guild] Limiting traceback to user code. Use 'guild --debug run ...' for full stack.
    Traceback (most recent call last):
    ...
    AttributeError: module 'tensorflow.summary' has no attribute 'FileWriter'
    <exit 1>
