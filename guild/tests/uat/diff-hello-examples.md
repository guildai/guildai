# Diff hello examples

These tests use the Guild `diff` command to compare runs.

We'll run them against the `hello` example:

    >>> cd(example("hello"))

Let's run `hello` twice, each time with a different msg.

    >>> quiet("guild run -y hello msg='msg is foo'")
    >>> quiet("guild run -y hello msg='msg is bar'")

Here are our last two:

    >>> run("guild runs -n 2")
    [1:...]   hello  ...  completed  msg='msg is bar'
    [2:...]   hello  ...  completed  msg='msg is foo'
    <exit 0>

Let's use Guild `diff` to compare the two runs.

Run flags:

    >>> run("guild diff -f -c 'diff'")
    1c1
    < msg: msg is foo
    ---
    > msg: msg is bar
    <exit 0>

Run output:

    >>> run("guild diff -O -c 'diff'")
    1c1
    < msg is foo
    ---
    > msg is bar
    <exit 0>

Run generated output file:

    >>> run("guild diff --output -c 'diff'")
    1c1
    < msg is foo
    ---
    > msg is bar
    <exit 0>

Invalid diff command:

    >>> run("guild diff -c invalid-diff-cmd")
    guild: error running 'invalid-diff-cmd ... ...': ...No such file or directory...
    <exit 1>

Invalid diff command option - if the command can be run, Guild treats
it as success even if the command doesn't behave as expected:

    >>> run("guild diff -c 'diff --invalid-opt'")
    diff: unrecognized option ...--invalid-opt'
    diff: Try ...diff --help' for more information.
    <exit 0>
