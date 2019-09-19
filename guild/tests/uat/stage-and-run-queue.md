# Stage runs and run with queue

Use noisy example:

    >>> cd("examples/noisy")

Stage runs:

    >>> run("guild run noisy.py x=4 --stage -y", ignore="Refreshing")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run noisy.py x=5 --stage --label 'x is 5' -y")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run noisy.py x=6 --stage -y")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

Run `queue` once:

    >>> run("guild run queue run-once=yes -y")
    INFO: [queue] Found staged run ...
    INFO: [queue] Starting ...
    x: 4.000000
    noise: 0.1
    loss: ...
    INFO: [queue] Found staged run ...
    INFO: [queue] Starting ...
    x: 5.000000
    noise: 0.1
    loss: ...
    INFO: [queue] Found staged run ...
    INFO: [queue] Starting ...
    x: 6.000000
    noise: 0.1
    loss: ...
    <exit 0>

List runs:

    >>> run("guild runs", ignore="Showing")
    [1:...]   noisy.py  ...  completed  x=6
    [2:...]   noisy.py  ...  completed  x is 5
    [3:...]   noisy.py  ...  completed  x=4
    ...
    <exit 0>
