# Run GPUs

Sample script that prints out `CUDA_VISIBLE_DEVICES` env var.

    >>> project = mkdtemp()
    >>> set_guild_home(project)
    >>> cd(project)

    >>> write("test.py", """
    ... import os
    ... print(os.getenv("CUDA_VISIBLE_DEVICES"))
    ... """)

No GPU spec:

    >>> run("guild run test.py -y")
    ???None
    <exit 0>

Explicitly disable GPUs with `--no-gpus`:

    >>> run("guild run test.py --no-gpus -y")
    <BLANKLINE>
    <exit 0>

Specify GPUs with `--gpus`:

    >>> run("guild run test.py --gpus 0,1 -y")
    0,1
    <exit 0>

Specify both options:

    >>> run("guild run test.py --gpus 0,1 --no-gpus -y")
    guild: --no-gpus and --gpus cannot both be used
    Try 'guild run --help' for more information.
    <exit 1>

Stage using `--gpus`:

    >>> run("guild run test.py --run-id aaa --gpus 0,1 --stage -y")
    test.py staged as aaa
    To start the operation, use 'guild run --start aaa'
    <exit 0>

Start staged run:

    >>> run("guild run --start aaa -y")
    0,1
    <exit 0>

Stage again:

    >>> run("guild run test.py --run-id bbb --gpus 0,1 --stage -y")
    test.py staged as bbb
    To start the operation, use 'guild run --start bbb'
    <exit 0>

Start staged run with an alternative GPU spec:

    >>> run("guild run --start bbb --gpus 2 -y")
    2
    <exit 0>

Restart run with an alternative GPU spec:

    >>> run("guild run --restart bbb --no-gpus -y")
    <BLANKLINE>
    <exit 0>

Restart run with no GPU spec - Guild uses the originally specified GPU
spec:

    >>> run("guild run --restart bbb -y")
    0,1
    <exit 0>
