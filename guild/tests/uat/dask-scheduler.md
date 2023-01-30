
---
doctest: -PY37
---

# Dask Scheduler

Clear existing runs for our tests.

    >>> quiet("guild runs rm -y")

## Long Running Operation

Start a Dask scheduler in the background.

    >>> run("guild run dask:scheduler poll-interval=1 --background -y")
    dask:scheduler started in background as ... (pidfile ...)
    <exit 0>

Wait a moment and check scheduler output.

    >>> sleep(5)

    >>> run("guild cat --output")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    ...
    <exit 0>

Stage five runs, each run sleeping for 3 seconds.

    >>> cd(example("parallel-runs"))
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")

Wait 8 seconds for the runs to start and complete. If run in series,
the set of runs would take over 10 seconds to complete. The Dask
scheduler runs these concurrently so we expect them to be completed in
a little over two seconds. We use 8 seconds as a buffer and to
accommodate the scheduler poll interval of one second (see above).

    >>> sleep(8)

Check the run status.

    >>> run("guild runs -s")
    [1]  op              completed  sleep=2
    [2]  op              completed  sleep=2
    [3]  op              completed  sleep=2
    [4]  op              completed  sleep=2
    [5]  op              completed  sleep=2
    [6]  dask:scheduler  running    ...
    <exit 0>

Stop the sceduler.

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    <exit 0>

Wait a moment and check scheduler output. We can't be certain of the
order of log statements but we know there are five runs outputing
`Waiting for 2 second(s)`.

    >>> sleep(2)
    >>> run("guild cat -Fo scheduler --output")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    ...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster...
    <exit 0>

## Run Once

The Dask scheduler can be run once to process staged runs and then
exit.

First delete runs in preparation for tests.

    >>> quiet("guild runs rm -y")

This requires staged runs. We can use a batch to stage them in one command.

    >>> run("guild run op sleep=[2]*10 --stage-trials -y")
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    INFO: [guild] Staging trial ...: op (sleep=2)
    <exit 0>

Start a scheduler with 10 workers so we can process all ten trials in
parallel. We use `run-once` to process the staged runs and then exit.

    >>> run("guild run dask:scheduler workers=10 run-once=yes -y")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster with 10 workers
    ...
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... started...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Run ... completed...
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster...
    <exit 0>

The runs:

    >>> run("guild runs")
    [1:...]   op              ...  completed  sleep=2
    [2:...]   op              ...  completed  sleep=2
    [3:...]   op              ...  completed  sleep=2
    [4:...]   op              ...  completed  sleep=2
    [5:...]   op              ...  completed  sleep=2
    [6:...]   op              ...  completed  sleep=2
    [7:...]   op              ...  completed  sleep=2
    [8:...]   op              ...  completed  sleep=2
    [9:...]   op              ...  completed  sleep=2
    [10:...]  op              ...  completed  sleep=2
    [11:...]  dask:scheduler  ...  completed  ...
    <exit 0>

## Dashboard

Use `dashboard-address` to specify the IP address and/or port used for
the dashboard web app.

For these tests we need to install the `bokeh` library.

    >>> quiet("pip install bokeh")

### Explicit Port

Let's find a free port.

    >>> from guild import util
    >>> port = util.free_port(8787)

Start a scheduler with that port specified as the dashboard address.

    >>> run("guild run dask:scheduler dashboard-address=%i --background -y" % port)
    dask:scheduler started in background as ... (pidfile ...)
    <exit 0>

Wait for the scheduler to start.

    >>> sleep(5)

Show all output to confirm the scheduler is running as expected.

    >>> run("guild cat --output")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster
    ...
    INFO: [guild] ... Waiting for staged runs
    <exit 0>

Look for a line indicating that the dashboard is running on the expected port.

    >>> run("guild cat --output | grep -e 'Dashboard link: http://.*:%i/status'" % port)
    INFO: [guild] ... Dashboard link: http://.../status
    <exit 0>

Check availability of the dashboard HTTP service.

    >>> run("curl -ISs -X GET http://0.0.0.0:%i/status" % port)
    HTTP/1.1 200 OK
    ...
    <exit 0>

Stop the scheduler.

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    <exit 0>

### Disable Dashboard

Use False to disable the dashboard.

    >>> run("guild run dask:scheduler dashboard-address=no --background -y")
    dask:scheduler started in background as ... (pidfile ...)
    <exit 0>

Wait for the scheduler to start.

    >>> sleep(5)

Verify that the dashboard is disabled.

    >>> run("guild cat --output")
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Initializing Dask cluster...
    INFO: [guild] ... Dashboard link: <disabled>
    INFO: [guild] ... Waiting for staged runs
    <exit 0>

Stop the scheduler.

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    <exit 0>
