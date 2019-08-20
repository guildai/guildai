# Run Labels

Labels are used to help identify runs and differentiate them from
other runs. Run labels are set using a variety of rules, which are
demonstrated here.

For our tests, we'll use the `labels` sample project:

    >>> project = Project(sample("projects/labels"))

Here are some helper functions.

    >>> def run(op, label=None, batch_label=None, opt_flags=None, **kw):
    ...   project.run(op, flags=kw, label=label, batch_label=batch_label,
    ...               disable_plugins="all", opt_flags=opt_flags,
    ...               force_flags=True, quiet=True)

    >>> def print_last_run():
    ...   print_runs(1)

    >>> def print_runs(n):
    ...   runs = project.list_runs()[0:n]
    ...   project.print_runs(runs, labels=True)

## Default labels

A default label is a label that is not otherwise specified in an
operation definition or from a command line option. Guild uses default
labels for runs in the format:

    NAME1=VAL1 NAME2=VAL2 ...

where name and vals are of non-default flag values.

Here's an example.

Let's run the `op.py` script without setting any flags.

    >>> run("op.py")

In this case, we didn't change any flag values and so the label is
empty.

    >>> print_last_run()
    op.py

Let's specify a flag value.

    >>> run("op.py", i=2)

We modified one flag `i` - and this is reflected in the default label.

    >>> print_last_run()
    op.py  i=2

Here's a broader example: we redefine all flags.

    >>> run("op.py", i=2, f=3.0, b=False, s="hi")

    >>> print_last_run()
    op.py  b=no f=3.0 i=2 s=hi

If we set a flag value that is equal to the default value, that value
is NOT reflected in the default label, even though it appears in the
run command.

    >>> run("op.py", i=1, f=2.0, b=True, s="hi")

    >>> print_last_run()
    op.py  s=hi

## Explicit labels

When a label is provided by the user, it is always used, regardless of
flag values.

    >>> run("op.py", label="custom label", i=2)

    >>> print_last_run()
    op.py  custom label

We can include a reference to the flag value in the label.

    >>> run("op.py", label="i equals ${i}", i=2)

    >>> print_last_run()
    op.py  i equals 2

## Operation defined labels

If a label is defined for an operation, it is used by default if one
is not specified by the user.

We'll use the `op` operation, defined in the project Guild file, which
defines a label.

    >>> gf = guildfile.from_dir(sample("projects", "labels"))

    >>> gf.default_model["op"].label
    'i:${i}, f:${f}, b:${b}, s:${s}'

Let's run this operation without specifying flags.

    >>> run("op")

    >>> print_last_run()
    op  i:1, f:2.0, b:yes, s:hello

When we provide flag values, the label format isn't changed - but the
values do.

    >>> run("op", i=2, s="yo")

    >>> print_last_run()
    op  i:2, f:2.0, b:yes, s:yo

## Trial labels

When an operation is run as a batch trial, the same rules apply as
described above.

Let's run `op.py` in a batch to generate two trials:

    >>> run("op.py", i=[1,2], s="yello")

Let's list the last three runs, which include the batch and the two
trials:

    >>> print_runs(3)
    op.py   i=2 s=yello
    op.py   s=yello
    op.py+

Here's the same result running `op`:

    >>> run("op", i=[1,2], s="yello", b=False)

    >>> print_runs(3)
    op   i:2, f:2.0, b:no, s:yello
    op   i:1, f:2.0, b:no, s:yello
    op+

In this case, we specify an explicit label for the trials:

    >>> run("op", i=[1,2], label="i is ${i}")

    >>> print_runs(3)
    op   i is 2
    op   i is 1
    op+

## Batch labels

Labels for batch runs follow the same rules as for other runs.

We can see the default label for a grid search in the trial examples
above.

Let's force an optimizer flag (the name/value doesn't matter - just as
long as one is defined) to see how the default label is applied to a
batch run. We can run an empty batch by specifying an empty list for a
flag.

    >>> run("op.py", i=[], opt_flags={"foo": 123})

    >>> print_last_run()
    op.py+  foo=123

We can alternatively specify an explicit batch label:

    >>> run("op.py", i=[], opt_flags={"foo": 123}, batch_label="empty batch")

    >>> print_last_run()
    op.py+  empty batch

## Edge cases

Quoted numbers:

    >>> run("op.py", i="1")

    >>> print_last_run()
    op.py  i='1'

Values containing spaces:

    >>> run("op.py", s="hello there")

    >>> print_last_run()
    op.py  s='hello there'
