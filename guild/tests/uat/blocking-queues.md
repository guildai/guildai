# Blocking Queues

By default, a queue starts staged runs even when other runs are in
progress. Queues may be started, however, with the flag
`wait-for-running`, which causes them to block until other runs have
stopped. (This does not apply to running queues, which are ignored
when considering in in progress runs.)

For our tests, we delete existing runs.

    >>> quiet("guild runs rm -y")

Here's a project with a sample operation that waits for 5 seconds.

    >>> project_dir = mkdtemp()

    >>> write(path(project_dir, "sleep.py"), """
    ... import time
    ... seconds = 5
    ... time.sleep(seconds)
    ... """)

    >>> cd(project_dir)

To illustrate the default behavior, we stage two runs"

    >>> run("guild run sleep.py --stage -y")
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run sleep.py --stage -y")
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

The staged runs:

    >>> run("guild runs")
    [1:...]  sleep.py  ...  staged  seconds=5
    [2:...]  sleep.py  ...  staged  seconds=5
    <exit 0>

Next, start two queues. We use tags to identify each queue. We wait a
second in between starting the queues to order the resulting runs (for
deterministic tests).

    >>> run("guild run queue poll-interval=1 --tag q1 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

    >>> sleep(1)

    >>> run("guild run queue poll-interval=1 --tag q2 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait to let the queues start the staged runs.

    >>> sleep(8)

The current runs:

    >>> run("guild runs")
    [1:...]  sleep.py  ...  completed  seconds=5
    [2:...]  queue     ...  running    q2 poll-interval=1 run-once=no wait-for-running=no
    [3:...]  sleep.py  ...  completed  seconds=5
    [4:...]  queue     ...  running    q1 poll-interval=1 run-once=no wait-for-running=no
    <exit 0>

And the logs for each queue.

    >>> run("guild cat --output -Fl q1")
    INFO: [queue] ... Starting staged run ...
    INFO: [queue] ... Waiting for staged runs
    <exit 0>

    >>> run("guild cat --output -Fl q2")
    INFO: [queue] ... Starting staged run ...
    INFO: [queue] ... Waiting for staged runs
    <exit 0>

Note that each queue starts a staged run without waiting.

Next, we demonstrate queue behavior when `wait-for-running` is enabled
for queues.

Stop the queues:

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    <exit 0>

Delete the runs:

    >>> run("guild runs rm -y")
    Deleted 4 run(s)
    <exit 0>

Stage two runs:

    >>> run("guild run sleep.py --stage -y")
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run sleep.py --stage -y")
    sleep.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Start two queues, this time using `wait-for-running`. We delay
slightly after starting the first queue to let it start one of the
staged runs.

    >>> run("guild run queue poll-interval=1 wait-for-running=yes --tag q1 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait a moment to let the queue start one of the staged runs:

    >>> sleep(2)

At this point we have one run in progress and the other staged:

    >>> run("guild runs")
    [1:...]  sleep.py  ...  running  seconds=5
    [2:...]  queue     ...  running  q1 poll-interval=1 run-once=no wait-for-running=yes
    [3:...]  sleep.py  ...  staged   seconds=5
    <exit 0>

Output for the first queue:

    >>> run("guild cat --output -Fl q1")
    INFO: [queue] ... Starting staged run ...
    <exit 0>

Start the second queue:

    >>> run("guild run queue poll-interval=1 wait-for-running=yes --tag q2 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait a moment for the second queue to start and check for staged runs.

    >>> sleep(2)

At this point, the second queue will have detected that a run is
in-progress and defer starting the pending staged run until it's next
check.

    >>> run("guild cat --output -Fl q2")
    INFO: [queue] ... Found staged run ... (waiting for runs to finish: ...)
    ...
    <exit 0>

As we have a race condition for which queue starts the second staged
run, we can't assert which queue starts it. We wait, however, to
confirm that the second staged run is eventually started and finishes.

    >>> sleep(10)

Our runs:

    >>> run("guild runs")
    [1:...]  sleep.py  ...  completed  seconds=5
    [2:...]  queue     ...  running    q2 poll-interval=1 run-once=no wait-for-running=yes
    [3:...]  sleep.py  ...  completed  seconds=5
    [4:...]  queue     ...  running    q1 poll-interval=1 run-once=no wait-for-running=yes
    <exit 0>

Finally, stop the queues:

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    <exit 0>
