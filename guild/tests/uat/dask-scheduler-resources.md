---
doctest: -PY2_MACOS
---

# Dask Scheduler Resources

Clear existing runs for our tests.

    >>> quiet("guild runs rm -y")

We use a dynamically generated project for these tests.

    >>> project = mkdtemp()

    >>> cd(project)

    >>> write(path(project, "op.py"), """
    ... import os
    ... import time
    ...
    ... sleep = 1.0
    ... _run_id = os.getenv("RUN_ID")
    ... _cuda_devices = os.getenv("CUDA_VISIBLE_DEVICES")
    ... _gpus_desc = " (CUDA_VISIBLE_DEVICES=%s)" % _cuda_devices if _cuda_devices else ""
    ...
    ... print("Run %s start%s" % (_run_id, _gpus_desc))
    ... time.sleep(sleep)
    ... print("Run %s stop" % _run_id)
    ... """)

## Overview

Resources are used to limit runs to clusters that have available
resources. A resource identified by a name. When specified, resources
have numeric values that indicate available or required
resources. When specified for a cluster, the value indicates the
available named resource for the cluster. When specified for a run,
the value indicates the required named resoure.

Available resources are specified for clusters using the `resources`
flag.

Required resources are specified for a run using a tag in the format
`dask:<resources>`.

## Examples

Let's illustrate by staging two runs, each requiring 5 'foo'
resources (resource names are arbitrary).

    >>> quiet("guild run op.py sleep=2 --tag dask:foo=5 --stage -y")
    >>> quiet("guild run op.py sleep=2 --tag dask:foo=5 --stage -y")

Run the staged operations using a scheduler with 7 avaialble foo
resources. Because there isn't enough foo to run both operations
concurrently, each is run in series.

    >>> run("guild run dask:scheduler run-once=yes resources=foo=7 -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Cluster resources: foo=7
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Scheduling run ... (requires foo=5)
    INFO: [guild] ... Run ... started
    INFO: [guild] ... Scheduling run ... (requires foo=5)
    Run ... start
    Run ... stop
    INFO: [guild] ... Run ... completed
    INFO: [guild] ... Run ... started
    Run ... start
    Run ... stop
    INFO: [guild] ... Run ... completed
    INFO: [guild] ... Dask scheduler ran for ... seconds
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Let's rerun this scenario with a scheduler that has enough foo to run
two staged runs concurrently.

Stage two runs, each requiring 5 foo, as before.

    >>> quiet("guild run op.py sleep=2 --tag dask:foo=5 --stage -y")
    >>> quiet("guild run op.py sleep=2 --tag dask:foo=5 --stage -y")

This time, start a scheduler with 12 available foo.

    >>> run("guild run dask:scheduler run-once=yes resources=foo=12 -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    INFO: [guild] ... Dashboard link: ...
    INFO: [guild] ... Cluster resources: foo=12
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Scheduling run ... (requires foo=5)
    INFO: [guild] ... Run ... started
    INFO: [guild] ... Scheduling run ... (requires foo=5)
    INFO: [guild] ... Run ... started
    Run ... start
    Run ... start
    Run ... stop
    Run ... stop
    INFO: [guild] ... Run ... completed
    INFO: [guild] ... Run ... completed
    INFO: [guild] ... Dask scheduler ran for ... seconds
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

## Missing Resources

If a run is staged with a required Dask resource that is not
explicitly provided by a scheduler, the scheduler will ignore the
staged run as it cannot run it.

Stage a run with a foo requirement.

    >>> quiet("guild run op.py --tag dask:foo=5 --stage -y")

Run a scheduler without defining available foo.

    >>> run("guild run dask:scheduler run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Ignorning staged run ... (requires resources not defined for cluster: foo)
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Clear out runs for subsequent tests.

    >>> quiet("guild runs rm -y")

## Multiple Resources

More than one resource can be specified using additional
space-delimited name value pairs. Runs may use multiple tags as well.

Stage a run requiring three resources.

    >>> quiet("guild run op.py -t dask:foo=1 -t 'dask:bar=1 baz=1' --stage -y")

Start a scheduler that provides all three resources.

    >>> run("guild run dask:scheduler resources='foo=1 bar=1 baz=2' run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Scheduling run ... (requires bar=1 baz=1 foo=1)
    INFO: [guild] ... Run ... started
    Run ... start
    Run ... stop
    INFO: [guild] ... Run ... completed
    INFO: [guild] ... Dask scheduler ran for ... seconds
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Run the same scenario for with a scheduler with some missing resources.

    >>> quiet("guild run op.py -t dask:foo=1 -t 'dask:bar=1 baz=1' --stage -y")

    >>> run("guild run dask:scheduler resources='foo=1' run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Ignorning staged run ... (requires resources not defined for cluster: bar, baz)
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Delete runs for subsequent tests.

    >>> quiet("guild runs rm -y")

## Misspecified Resources

Dask resources must be in the format `<name>=<value>`. If they aren't
the scheduler logs a warning message and ignores the resource spec.

    >>> run("guild run dask:scheduler resources=foo run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    WARNING: [guild] ... Ignoring invalid dask resources spec 'foo': parts must be in format KEY=VAL
    INFO: [guild] ... Initializing Dask cluster
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Similarly, the scheduler logs a warning and ignores invalid run resources.

    >>> quiet("guild run op.py --stage --tag dask:bar -y")

    >>> run("guild run dask:scheduler run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Processing staged runs
    WARNING: [guild] ... Ignoring invalid dask resources spec 'bar': parts must be in format KEY=VAL
    INFO: [guild] ... Scheduling run ...
    INFO: [guild] ... Run ... started
    Run ... start
    Run ... stop
    INFO: [guild] ... Run ... completed
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Delete runs for subsequent tests.

    >>> quiet("guild runs rm -y")

## GPU Scheduling

A Dask scheduler can be used to limit operations to running in series
on GPUs.

- Start a scheduler with resources for each GPU. The numeric value
  should be either the maximium number of runs for each GPU or the
  total GPU memory.

- Stage runs using the `--gpus` option and a tag that specifies the
  required GPU resource. If the scheduler resource is the number of
  concurrent runs, use the value 1 with the applicable GPU name. If
  the scheduler resource is the GPU memory, specify the amount of
  memory required by the operation on the applicable GPU.

For these tests with use the resource identifiers 'gpu0' and 'gpu1' to
identify each GPU resource.

Stage two runs on GPU 0. These should run in series.

    >>> quiet("guild run op.py --run-id=aaa sleep=2 --gpus 0 --tag dask:gpu0=1 --stage -y")
    >>> quiet("guild run op.py --run-id=bbb sleep=2 --gpus 0 --tag dask:gpu0=1 --stage -y")

Stage a run that requires both GPUs. This run should run only after
the two previous runs finish.

    >>> quiet("guild run op.py --run-id=ccc sleep=2 --gpus 0,1 --tag dask:'gpu0=1 gpu1=1' --stage -y")

Stage a run that requires GPU 1. This should run in parallel alongside
the first staged run for GPU 0.

NOTE: The behavior from Dask.distributed is unexpected. The following
does not run until after the previous run is completed, even though it
could be moved up in priority to take advantage of the fact that gpu1
is not occupied when this is scheduled.

    >>> quiet("guild run op.py --run-id=ddd sleep=2 --gpus 1 --tag dask:gpu1=1 --stage -y")

Run a scheduler that defines resources for the two GPUs. It allows
only one run per GPU.

    >>> run("guild run dask:scheduler resources='gpu0=1 gpu1=1' run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    INFO: [guild] ... Dashboard link: ...
    INFO: [guild] ... Cluster resources: gpu0=1 gpu1=1
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Scheduling run aaa (requires gpu0=1)
    INFO: [guild] ... Run aaa started
    INFO: [guild] ... Scheduling run bbb (requires gpu0=1)
    INFO: [guild] ... Scheduling run ccc (requires gpu0=1 gpu1=1)
    INFO: [guild] ... Scheduling run ddd (requires gpu1=1)
    Run aaa start (CUDA_VISIBLE_DEVICES=0)
    Run aaa stop
    INFO: [guild] ... Run aaa completed
    INFO: [guild] ... Run bbb started
    Run bbb start (CUDA_VISIBLE_DEVICES=0)
    Run bbb stop
    INFO: [guild] ... Run bbb completed
    INFO: [guild] ... Run ccc started
    Run ccc start (CUDA_VISIBLE_DEVICES=0,1)
    Run ccc stop
    INFO: [guild] ... Run ccc completed
    INFO: [guild] ... Run ddd started
    Run ddd start (CUDA_VISIBLE_DEVICES=1)
    Run ddd stop
    INFO: [guild] ... Run ddd completed
    INFO: [guild] ... Dask scheduler ran for ... seconds
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

NOTE: Once again, the output here is unexpected or at least
suboptimal. Run 'ddd' could be stated alongside run 'aaa'. Instead,
Dask is serializing the runs that require gpu0 first.

In light of this surprise, a user should take care when ordering
staged runs to support parallelism.

NOTE: Guild could address this, possibly, by ordering the submits to
the client to take advantage of possible parallelism.

The above example can be re-ordered as follows the take advantage of
parallelism.

    >>> quiet("guild run op.py --run-id=aaa sleep=2 --gpus 0 --tag dask:gpu0=1 --stage -y")
    >>> quiet("guild run op.py --run-id=ddd sleep=2 --gpus 1 --tag dask:gpu1=1 --stage -y")
    >>> quiet("guild run op.py --run-id=bbb sleep=2 --gpus 0 --tag dask:gpu0=1 --stage -y")
    >>> quiet("guild run op.py --run-id=ccc sleep=2 --gpus 0,1 --tag dask:'gpu0=1 gpu1=1' --stage -y")

Run the scheduler as before.

    >>> run("guild run dask:scheduler resources='gpu0=1 gpu1=1' run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    INFO: [guild] ... Dashboard link: ...
    INFO: [guild] ... Cluster resources: gpu0=1 gpu1=1
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Scheduling run aaa (requires gpu0=1)
    INFO: [guild] ... Run aaa started
    INFO: [guild] ... Scheduling run ddd (requires gpu1=1)
    INFO: [guild] ... Scheduling run bbb (requires gpu0=1)
    INFO: [guild] ... Run ddd started
    INFO: [guild] ... Scheduling run ccc (requires gpu0=1 gpu1=1)
    Run aaa start (CUDA_VISIBLE_DEVICES=0)
    Run ddd start (CUDA_VISIBLE_DEVICES=1)
    Run aaa stop
    Run ddd stop
    INFO: [guild] ... Run aaa completed
    INFO: [guild] ... Run bbb started
    INFO: [guild] ... Run ddd completed
    Run bbb start (CUDA_VISIBLE_DEVICES=0)
    Run bbb stop
    INFO: [guild] ... Run bbb completed
    INFO: [guild] ... Run ccc started
    Run ccc start (CUDA_VISIBLE_DEVICES=0,1)
    Run ccc stop
    INFO: [guild] ... Run ccc completed
    INFO: [guild] ... Dask scheduler ran for ... seconds
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>
