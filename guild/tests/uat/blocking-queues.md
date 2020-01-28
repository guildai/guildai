# Blocking Queues

By default a queue will only start a staged run if there are no other
non-queue runs in progress. The rationale is that it's safer to assume
that any given run requires the full system than to assume otherwise.

Therefore `ignore-running` is `no` by default --- i.e. a queue waits
for runs to complete before starting available staged runs.

Delete runs in preparation for these tests.

    >>> quiet("guild runs rm -y")

Let's create a project to test staged runs using queues.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "sleep.py"), """
    ... import time
    ... seconds = 5
    ... time.sleep(seconds)
    ... """)

    >>> cd(project_dir)

Start a queue in the background.

    >>> run("guild run queue poll-interval=1 --tag q1 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Stage two runs.

    >>> for _ in range(2):
    ...     run("guild run sleep.py --stage -y")
    Refreshing flags...
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

At this point our queue will start one of the two runs.

Let's start a second queue with label `q2` so we can explicitly
reference it later.

    >>> run("guild run queue poll-interval=1 --tag q2 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait for the runs to complete.

    >>> sleep(15)

Here are our runs:

    >>> run("guild runs")
    [1:...]  sleep.py  ...  completed  seconds=5
    [2:...]  queue     ...  running    q2 ignore-running=no poll-interval=1 run-once=no
    [3:...]  sleep.py  ...  completed  seconds=5
    [4:...]  queue     ...  running    q1 ignore-running=no poll-interval=1 run-once=no
    <exit 0>

The logs of our second queue should indicate that it was waiting on
runs to complete.

    >>> run("guild cat --output -l q2")
    INFO: [queue] ... Found staged run ... (waiting for runs to finish: ...)
    ...
    <exit 0>

Stop the queues:

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    <exit 0>

Confirm there are no active runs:

    >>> run("guild runs --running")
    <exit 0>
