# TensorFlow 2.0

These tests use `guild.tfevent`, which requires that we call
`_ensure_tb_logging_patched` to supress TensorFlow logging noise.

    >>> from guild import tfevent
    >>> tfevent._ensure_tb_logging_patched()

Install TensorFlow 2:

    >>> quiet("pip install 'tensorflow>=2.0.0,<2.1' --upgrade",
    ...     ignore="DEPRECATION",
    ...     timeout=120)

NOTE: We install 2.0.0 here because `tensorflow` 2.1 appears to be
enabling CUDA support, which introduces variability across out test
platforms.

TODO: Invetigate ways to disable CUDA support in `tensorflow` to avoid
GPU logged messages for our tests.

NOTE: This command changes the UAT runtime to use a new version of
TensorFlow. The version does not support GPU.

Check:

    >>> run("guild check --offline --tensorflow")
    guild_version:             ...
    tensorboard_version:       2.0.2
    tensorflow_version:        2.0...
    tensorflow_cuda_support:   no
    tensorflow_gpu_available:  no
    ...
    <exit 0>

We'll use the `tensorflow-vers` example project for our tests.

    >>> cd(example("tensorflow-versions"))

## Log system summaries with scalars

Run `summary2` op, which uses the TF 2.x API to log some scalars.

    >>> logdir = mkdtemp()
    >>> run("guild run -y summary2 logdir='%s'" % logdir,
    ...     ignore=["I tensorflow/", "NVIDIA-SMI has failed"])
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
    Traceback (most recent call last):
    ...
    AttributeError: ... has no attribute 'FileWriter'
    <exit 1>
