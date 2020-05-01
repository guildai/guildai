# No run output

Use the `get-started` example for these tests.

    >>> cd(example("get-started"))

The environment variable `NO_RUN_OUTPUT` tells Guild to not capture
and save run output. Output is still displayed on stdout and stderr
streams.

First, the case when `NO_RUN_OUTPUT` is not set.

    >>> run("guild run train.py -y")
    x: 0.100000
    noise: 0.100000
    loss: ...
    <exit 0>

Output files generated:

    >>> run("guild ls -a -p .guild/output")
    ???/.guild/runs/...:
      .guild/output
      .guild/output.index
    <exit 0>

And output:

    >>> run("guild cat --output")
    x: 0.100000
    noise: 0.100000
    loss: ...
    <exit 0>

Next, set `NO_RUN_OUTPUT` to `1`:

    >>> run("NO_RUN_OUTPUT=1 guild run train.py -y")
    x: 0.100000
    noise: 0.100000
    loss: ...
    <exit 0>

The generated output files:

    >>> run("guild ls -a -p .guild/output")
    ???/.guild/runs/...:
    <exit 0>

And output:

    >>> run("guild cat --output")
    guild: .../.guild/output does not exist
    <exit 1>
