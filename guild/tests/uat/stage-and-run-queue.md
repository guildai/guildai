# Stage runs and run with queue

Use noisy example:

    >>> cd(example("get-started"))

Delete runs for tests.

    >>> quiet("guild runs rm -y")

Stage runs:

    >>> run("guild run train.py x=4 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild run train.py x=5 --stage --label 'x is 5' -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'

    >>> run("guild run train.py x=6 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'

View the list of staged runs:

    >>> run("guild runs -s")
    [1]  train.py  staged  noise=0.1 x=6
    [2]  train.py  staged  x is 5
    [3]  train.py  staged  noise=0.1 x=4

Run `queue` once:

    >>> run("guild run queue run-once=yes -y")
    INFO: [guild] ... Starting queue
    INFO: [guild] ... Processing staged runs
    INFO: [guild] ... Starting staged run ...
    x: 4.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] ... Starting staged run ...
    x: 5.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] ... Starting staged run ...
    x: 6.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] ... Stopping queue
    Deleting interim run ... ('queue' is configured for deletion on success)

List runs:

    >>> run("guild runs -s")
    [1]  train.py  completed  noise=0.1 x=6
    [2]  train.py  completed  x is 5
    [3]  train.py  completed  noise=0.1 x=4

Stage another run. We want to test the queue being run from another
directory.

    >>> run("guild run train.py x=7 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'

Start the queue from the workspace root.

    >>> cd(WORKSPACE)

    >>> run("guild run queue run-once=yes -y")
    INFO: [guild] ... Starting queue
    INFO: [guild] ... Starting staged run ...
    x: 7.000000
    noise: 0.100000
    loss: ...
    INFO: [guild] ... Stopping queue
    Deleting interim run ... ('queue' is configured for deletion on success)

    >>> run("guild runs -s")
    [1]  train.py (.../examples/get-started)  completed  noise=0.1 x=7
    [2]  train.py (.../examples/get-started)  completed  noise=0.1 x=6
    [3]  train.py (.../examples/get-started)  completed  x is 5
    [4]  train.py (.../examples/get-started)  completed  noise=0.1 x=4
