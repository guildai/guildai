# Run info after `mnist-softmax` train

Use `guild runs info` to show information about the latest run:

    >>> run("guild runs info")
    id: ...
    operation: mnist/mnist-softmax:train
    status: completed
    started: ...
    stopped: ...
    rundir: ...
    command: python -um guild.op_main softmax --epochs 1 --batch-size 100
    exit_status: 0
    pid: (not running)
    <exit 0>
