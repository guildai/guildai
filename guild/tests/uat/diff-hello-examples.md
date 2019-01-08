# Diff hello examples

These tests use the Guild `diff` command to compare runs.

We'll run them against the `hello` example:

    >>> cd("examples/hello")

Let's run `from-flag` twice, each time with a different message.

    >>> quiet("guild run -y from-flag message='message is foo'")
    >>> quiet("guild run -y from-flag message='message is bar'")

Here are our last two:

    >>> run("guild runs", ignore="Showing the first 20")
    [1:...]   hello:from-flag  ...  completed
    [2:...]   hello:from-flag  ...  completed
    ...<exit 0>

Let's use Guild `diff` to compare the two runs.

Run flags:

    >>> run("guild diff -g -c 'diff'")
    1c1
    < message: message is foo
    ---
    > message: message is bar
    <exit 0>

Run output:

    >>> run("guild diff -O -c 'diff'")
    1c1
    < message is foo
    ---
    > message is bar
    <exit 0>

Run generated output file:

    >>> run("guild diff -p output -c 'diff'")
    1c1
    < message is foo
    \ No newline at end of file
    ---
    > message is bar
    \ No newline at end of file
    <exit 0>
