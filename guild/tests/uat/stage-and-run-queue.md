# Stage runs and run with queue

Use noisy example:

    >>> cd(example("get-started"))

Delete runs for tests.

    >>> quiet("guild runs rm -y")

Stage runs:

    >>> run("guild run train.py x=4 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run train.py x=5 --stage --label 'x is 5' -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run train.py x=6 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

View the list of staged runs:

    >>> run("guild runs")
    [1:...]  train.py  ...  staged  noise=0.1 x=6
    [2:...]  train.py  ...  staged  x is 5
    [3:...]  train.py  ...  staged  noise=0.1 x=4
    <exit 0>

Run `queue` once:

    >>> run("guild run queue run-once=yes -y")
    INFO: [queue] ... Processing staged runs
    INFO: [queue] ... Starting staged run ...
    x: 4.000000
    noise: 0.100000
    loss: ...
    INFO: [queue] ... Starting staged run ...
    x: 5.000000
    noise: 0.100000
    loss: ...
    INFO: [queue] ... Starting staged run ...
    x: 6.000000
    noise: 0.100000
    loss: ...
    <exit 0>

List runs:

    >>> run("guild runs")
    [1:...]  train.py  ...  completed  noise=0.1 x=6
    [2:...]  train.py  ...  completed  x is 5
    [3:...]  train.py  ...  completed  noise=0.1 x=4
    [4:...]  queue     ...  completed  poll-interval=10 run-once=yes wait-for-running=no
    <exit 0>

Stage another run. We want to test the queue being run from another
directory.

    >>> run("guild run train.py x=7 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Start the queue from the workspace root.

    >>> cd(WORKSPACE)
    >>> run("guild run queue run-once=yes -y")
    INFO: [queue] ... Starting staged run ...
    x: 7.000000
    noise: 0.100000
    loss: ...
    <exit 0>
