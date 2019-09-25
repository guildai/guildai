# Stage runs

Stage runs for the noisy example.

    >>> cd("examples/noisy")

Delete runs in preparation for these tests.

    >>> quiet("guild runs rm -y")

Stage runs:

    >>> run("guild run noisy.py x=1 --stage -y", ignore="Refreshing")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run noisy.py x=2 --stage --label 'x is 2' -y")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

    >>> run("guild run noisy.py x=3 --stage -y")
    noisy.py is staged as ...
    To run the operation, use 'guild run --start ...'
    <exit 0>

List staged runs:

    >>> run("guild runs -o noisy")
    [1:...]  noisy.py  ...  staged  x=3
    [2:...]  noisy.py  ...  staged  x is 2
    [3:...]  noisy.py  ...  staged  x=1
    <exit 0>

Show latest staged run:

    >>> run("guild runs info --staged")
    id: ...
    operation: noisy.py
    from: .../examples/noisy
    status: staged
    started: ...
    stopped:
    marked: no
    label: x=3
    sourcecode_digest: ...
    run_dir: .../.guild/runs/...
    command: ... -um guild.op_main noisy --noise 0.1 --x 3
    exit_status:
    pid:
    flags:
      noise: 0.1
      x: 3
    scalars:
    <exit 0>

List files for latest run:

    >>> run("guild ls -a")
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
      .guild/attrs/objective
      .guild/attrs/opdef
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/user
      .guild/opref
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/noisy.py
      .guild/sourcecode/noisy2.py
      .guild/sourcecode/requirements.txt
    <exit 0>

Run the latest three staged runs:

    >>> staged = list(gapi.runs_list(staged=True))[:3]
    >>> for staged_run in staged:
    ...     run("guild run --start %s -y" % staged_run.id)
    Starting ...
    x: 3.000000
    noise: 0.1
    loss: ...
    <exit 0>
    Starting ...
    x: 2.000000
    noise: 0.1
    loss: ...
    <exit 0>
    Starting ...
    x: 1.000000
    noise: 0.1
    loss: ...
    <exit 0>

List runs:

    >>> run("guild runs", ignore="Showing")
    [1:...]   noisy.py  ...  completed  x=1
    [2:...]   noisy.py  ...  completed  x is 2
    [3:...]   noisy.py  ...  completed  x=3
    <exit 0>
