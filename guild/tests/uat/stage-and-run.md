# Stage runs

Stage runs for the train example.

    >>> cd(example("get-started"))

Delete runs in preparation for these tests.

    >>> quiet("guild runs rm -y")

Stage runs:

    >>> run("guild run train.py x=1 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run train.py x=2 --stage --label 'x is 2' -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run train.py x=3 --stage -y")
    train.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

List staged runs:

    >>> run("guild runs -Fo train")
    [1:...]  train.py  ...  staged  noise=0.1 x=3
    [2:...]  train.py  ...  staged  x is 2
    [3:...]  train.py  ...  staged  noise=0.1 x=1
    <exit 0>

Show latest staged run:

    >>> run("guild runs info --staged")
    id: ...
    operation: train.py
    from: .../get-started
    status: staged
    started: ...
    stopped:
    marked: no
    label: noise=0.1 x=3
    sourcecode_digest: ...
    run_dir: .../.guild/runs/...
    command: ... -um guild.op_main train --noise 0.1 --x 3
    exit_status:
    pid:
    tags:
    flags:
      noise: 0.1
      x: 3
    scalars:
    <exit 0>

List files for latest run:

    >>> run("guild ls -a")  # doctest: +REPORT_UDIFF
    ???/.guild/runs/...:
      .guild/
      .guild/ENV
      .guild/STAGED
      .guild/attrs/
      .guild/attrs/cmd
      .guild/attrs/deps
      .guild/attrs/flags
      .guild/attrs/host
      .guild/attrs/id
      .guild/attrs/initialized
      .guild/attrs/label
      .guild/attrs/op
      .guild/attrs/pip_freeze
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/user
      .guild/attrs/user_flags
      .guild/attrs/vcs_commit
      .guild/opref
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/train.py
    <exit 0>

Run the latest three staged runs:

    >>> staged = list(gapi.runs_list(staged=True))[:3]
    >>> for staged_run in staged:
    ...     run("guild run --start %s -y" % staged_run.id)
    x: 3.000000
    noise: 0.100000
    loss: ...
    <exit 0>
    x: 2.000000
    noise: 0.100000
    loss: ...
    <exit 0>
    x: 1.000000
    noise: 0.100000
    loss: ...
    <exit 0>

List runs:

    >>> run("guild runs", ignore="Showing")
    [1:...]   train.py  ...  completed  noise=0.1 x=1
    [2:...]   train.py  ...  completed  x is 2
    [3:...]   train.py  ...  completed  noise=0.1 x=3
    <exit 0>
