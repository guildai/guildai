# Labels

These tests illustrate the various methods of setting a run label.

We use the hello example:

    >>> cd(example("hello"))

Let's clear existing runs:

    >>> quiet("guild runs rm -y")

And general a run that we can label:

    >>> quiet("guild run hello -y")

Default label:

    >>> run("guild runs")
    [1:...]  hello  ...  completed  msg='Hello Guild!'
    <exit 0>

Prepend to the label:

    >>> run("guild label -p foo -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  foo msg='Hello Guild!'
    <exit 0>

Append to the label:

    >>> run("guild label -a 'bar baz' -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  foo msg='Hello Guild!' bar baz
    <exit 0>

Remove part of the label:

    >>> run("guild label -rm foo -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  msg='Hello Guild!' bar baz
    <exit 0>

When removing a value from a label, the value must match a complete
sequence of space-delimited tokens. Values that match within a token
will not be removed. For example, removing the character 'a`:

    >>> run("guild label -rm a -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  msg='Hello Guild!' bar baz
    <exit 0>

A removed value may span multiple tokens:

    >>> run("guild label --remove 'bar baz' -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  msg='Hello Guild!'
    <exit 0>

And again:

    >>> run("guild label --remove \"msg='Hello Guild!'\" -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed
    <exit 0>

Set the entire label:

    >>> run("guild label -s 'hello goodbye' -y")
    Labeled 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed  hello goodbye
    <exit 0>

Clear the entire label:

    >>> run("guild label -c -y")
    Cleared label for 1 run(s)
    <exit 0>

    >>> run("guild runs")
    [1:...]  hello  ...  completed
    <exit 0>
