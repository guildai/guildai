---
doctest: -PY2_MACOS
---

# Dask Scheduler Resources

Clear existing runs for our tests.

    >>> quiet("guild runs rm -y")

We use the `parallel-runs` example for runs.

    >>> cd(example("parallel-runs"))

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

    >>> quiet("guild run sleep2.py seconds=2 --tag dask:foo=5 --stage -y")
    >>> quiet("guild run sleep2.py seconds=2 --tag dask:foo=5 --stage -y")

    >>> run("guild runs")
    [1:...]  sleep2.py  ...  staged  dask:foo=5 seconds=2
    [2:...]  sleep2.py  ...  staged  dask:foo=5 seconds=2
    <exit 0>

Run the staged operations using a scheduler with 7 avaialble foo
resources. Because there isn't enough foo to run both operations
concurrently, each is run in series.

    >>> run("guild run dask:scheduler run-once=yes resources=foo=7 -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Cluster resources: foo=7
    ...
    INFO: [guild] ... Starting staged run ... (requires foo=5)
    INFO: [guild] ... Starting staged run ... (requires foo=5)
    Run ... starting
    Run ... stopping
    Run ... starting
    Run ... stopping
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Let's rerun this scenario with a scheduler that has enough foo to run
two staged runs concurrently.

Stage two runs, each requiring 5 foo, as before.

    >>> quiet("guild run sleep2.py seconds=2 --tag dask:foo=5 --stage -y")
    >>> quiet("guild run sleep2.py seconds=2 --tag dask:foo=5 --stage -y")

    >>> run("guild runs")
    [1:...]  sleep2.py       ...  staged     dask:foo=5 seconds=2
    [2:...]  sleep2.py       ...  staged     dask:foo=5 seconds=2
    [3:...]  sleep2.py       ...  completed  dask:foo=5 seconds=2
    [4:...]  sleep2.py       ...  completed  dask:foo=5 seconds=2
    [5:...]  dask:scheduler  ...  completed  ...

This time, start a scheduler with 12 available foo.

    >>> run("guild run dask:scheduler run-once=yes resources=foo=12 -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Cluster resources: foo=12
    ...
    INFO: [guild] ... Starting staged run ... (requires foo=5)
    INFO: [guild] ... Starting staged run ... (requires foo=5)
    Run ... starting
    Run ... starting
    Run ... stopping
    Run ... stopping
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

## Missing Resources

If a run is staged with a required Dask resource that is not
explicitly provided by a scheduler, the scheduler will ignore the
staged run as it cannot run it.

Stage a run with a foo requirement.

    >>> quiet("guild run sleep2.py --tag dask:foo=5 --stage -y")

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

    >>> quiet("guild run op -t dask:foo=1 -t 'dask:bar=1 baz=1' --stage -y")

Start a scheduler that provides all three resources.

    >>> run("guild run dask:scheduler resources='foo=1 bar=1 baz=2' run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Starting staged run ... (requires bar=1 baz=1 foo=1)
    Waiting 1 second(s)
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Run the same scenario for with a scheduler with some missing resources.

    >>> quiet("guild run op -t dask:foo=1 -t 'dask:bar=1 baz=1' --stage -y")

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
    INFO: [guild] ... Initializing cluster
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>

Similarly, the scheduler logs a warning and ignores invalid run resources.

    >>> quiet("guild run op --stage --tag dask:bar -y")

    >>> run("guild run dask:scheduler run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    ...
    INFO: [guild] ... Processing staged runs
    WARNING: [guild] ... Ignoring invalid dask resources spec 'bar': parts must be in format KEY=VAL
    INFO: [guild] ... Starting staged run ...
    Waiting 1 second(s)
    ...
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>
