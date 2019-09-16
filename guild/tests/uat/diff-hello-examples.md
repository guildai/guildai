# Diff hello examples

These tests use the Guild `diff` command to compare runs.

We'll run them against the `hello` example:

    >>> cd("examples/hello")

Let's run `from-flag` twice, each time with a different message.

    >>> quiet("guild run -y from-flag message='message is foo'")
    >>> quiet("guild run -y from-flag message='message is bar'")

Here are our last two:

    >>> run("guild runs", ignore="Showing the first 20")
    [1:...]   hello:from-flag  ...  completed  message='message is bar'
    [2:...]   hello:from-flag  ...  completed  message='message is foo'
    ...<exit 0>

Let's use Guild `diff` to compare the two runs.

Run flags:

    >>> run("guild diff -g -m 'diff'")
    1c1
    < message: message is foo
    ---
    > message: message is bar
    <exit 0>

Run output:

    >>> run("guild diff -O -m 'diff'")
    1c1
    < message is foo
    ---
    > message is bar
    <exit 0>

Run generated output file:

    >>> run("guild diff -p output -m 'diff'")
    1c1
    < message is foo
    ---
    > message is bar
    <exit 0>

Invalid diff command:

    >>> run("guild diff -m invalid-diff-cmd")
    guild: error running 'invalid-diff-cmd ... ...': ...No such file or directory...
    <exit 1>

Invalid diff command option - if the command can be run, Guild treats
it as success even if the command doesn't behave as expected:

    >>> run("guild diff -m 'diff --invalid-opt'")
    diff: unrecognized option ...--invalid-opt'
    diff: Try ...diff --help' for more information.
    <exit 0>
