# Dask Scheduler

Clear existing runs for our tests.

    >>> quiet("guild runs rm -y")

Start a Dask scheduler in the background.

    >>> run("guild run dask:scheduler poll-interval=1 --background -y")
    dask:scheduler started in background as ... (pidfile ...)
    <exit 0>

Wait a moment and check scheduler output.

    >>> sleep(2)
    >>> run("guild cat --output")
    INFO: [guild] ... Initializing Dask cluster
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Waiting for staged runs
    <exit 0>

Stage five runs, each run sleeping for 3 seconds.

    >>> cd(example("parallel-runs"))
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")
    >>> quiet("guild run op sleep=2 --stage -y")

Wait 6 seconds for the runs to start and complete. If run in series,
the set of runs would take over 10 seconds to complete. The Dask
scheduler runs these concurrently so we expect them to be completed in
a little over two seconds. We use 6 seconds as a buffer and to
accommodate the scheduler poll interval of one second (see above).

    >>> sleep(6)

Check the run status.

    >>> run("guild runs")
    [1:...]  op         ...  completed  sleep=2
    [2:...]  op         ...  completed  sleep=2
    [3:...]  op         ...  completed  sleep=2
    [4:...]  op         ...  completed  sleep=2
    [5:...]  op         ...  completed  sleep=2
    [6:...]  scheduler  ...  running    poll-interval=1 run-once=no wait-for-running=no
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
    INFO: [guild] ... Initializing Dask cluster
    INFO: [guild] ... Starting Dask scheduler
    INFO: [guild] ... Waiting for staged runs
    INFO: [guild] ... Starting staged run ...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    Waiting 2 second(s)...
    INFO: [guild] ... Stopping Dask scheduler
    INFO: [guild] ... Stopping Dask cluster
    <exit 0>
