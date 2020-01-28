# Concurrent Queues

Multiple queues may be started to process runs concurrently. Each
queue must be started with the `ignore-running` flag.

Delete runs in preparation for these tests.

    >>> quiet("guild runs rm -y")

Start three queues in the background, each with `ignore-running` set
to `yes`:

    >>> for _ in range(3):
    ...     run("guild run queue ignore-running=yes poll-interval=1 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>
    queue:queue started in background as ... (pidfile ...)
    <exit 0>
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait a moment for the queues:

    >>> sleep(5)

Current runs:

    >>> run("guild runs")
    [1:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    [2:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    [3:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    <exit 0>

Let's create a project to test staged runs using queues.

    >>> project_dir = mkdtemp()
    >>> write(path(project_dir, "sleep.py"), """
    ... import time
    ... seconds = 10
    ... time.sleep(seconds)
    ... """)

Stage four runs - three will be started within one second (poll
interval of each of the queues) and the fourth started when a queue is
empty, 10 seconds later.

   >>> for _ in range(4):
   ...     run("guild -C '%s' run sleep.py --stage -y" % project_dir)
    Refreshing flags...
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Wait for the runs to start.

    >>> sleep(5)

Let's view our runs by status. First the staged runs:

    >>> run("guild runs --staged")
    [1:...]  sleep.py (...)  ...  staged  seconds=10
    <exit 0>

We have one staged runs because we've started one more run than we
have queues.

Now the running runs:

    >>> run("guild runs --running")
    [1:...]  sleep.py (...)  ...  running  seconds=10
    [2:...]  sleep.py (...)  ...  running  seconds=10
    [3:...]  sleep.py (...)  ...  running  seconds=10
    [4:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    [5:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    [6:...]  queue  ...  running  ignore-running=yes poll-interval=1 run-once=no
    <exit 0>

Wait the duration of the sleep operation.

    >>> sleep(10)

At least one run will have completed and we should no longer have any
staged runs.

    >>> run("guild runs --staged")
    <BLANKLINE>
    <exit 0>

Our list of runs:

    >>> run("guild runs")
    [1:...]  sleep.py (...)  ...  running    seconds=10
    [2:...]  sleep.py (...)  ...  completed  seconds=10
    [3:...]  sleep.py (...)  ...  completed  seconds=10
    [4:...]  sleep.py (...)  ...  completed  seconds=10
    [5:...]  queue           ...  running  ignore-running=yes poll-interval=1 run-once=no
    [6:...]  queue           ...  running  ignore-running=yes poll-interval=1 run-once=no
    [7:...]  queue           ...  running  ignore-running=yes poll-interval=1 run-once=no
    <exit 0>

Stop all runs:

    >>> run("guild runs stop -y")
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    <exit 0>
