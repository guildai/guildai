# Guild Example: shell-script

    >>> cd(example("languages"))

Default flags:

    >>> run("guild run bash -y")
    Train: lr=0.1 bs=100
    loss: 0.1
    <exit 0>

Modified flags:

    >>> run("guild run bash learning-rate=0.001 batch-size=500 -y")
    Train: lr=0.001 bs=500
    loss: 0.1
    <exit 0>

Script using env vars:

    >>> run("guild run bash-2 batch-size=5000 -y")
    Train: lr=0.1 bs=5000
    loss: 0.1
    <exit 0>

Runs:

    >>> run("guild runs -n3")
    [1:...]  bash-2  ...  completed  batch-size=5000 learning-rate=0.1
    [2:...]  bash    ...  completed  batch-size=500 learning-rate=0.001
    [3:...]  bash    ...  completed  batch-size=100 learning-rate=0.1
    <exit 0>

Compare:

    >>> run("guild compare -n3 -t -cc .label,loss")
    run  label                               loss
    ...  batch-size=5000 learning-rate=0.1   0.100000
    ...  batch-size=500 learning-rate=0.001  0.100000
    ...  batch-size=100 learning-rate=0.1    0.100000
    <exit 0>
