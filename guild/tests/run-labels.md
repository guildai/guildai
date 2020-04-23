# Run Labels

Labels are used to help identify runs and differentiate them from
other runs. Run labels are set using a variety of rules, which are
demonstrated here.

For our tests, we'll use the `labels` sample project:

    >>> project = Project(sample("projects/labels"))

Here are some helper functions.

    >> def run(opspec=None, label=None, batch_label=None, tag=None, batch_tag=None,
    ...         opt_flags=None, restart=None, **flags):
    ...   project.run(opspec, flags=flags, label=label, batch_label=batch_label,
    ...               tag=tag, batch_tag=batch_tag, opt_flags=opt_flags, restart=restart,
    ...               force_flags=True, quiet=True)

    >> def print_last_run():
    ...   print_runs(1)

    >> def print_runs(n):
    ...   runs = project.list_runs()[0:n]
    ...   project.print_runs(runs, labels=True)

## Default labels

Guild uses flag values to generate default labels in the format:

    NAME1=VAL1 NAME2=VAL2 ...

Prior to 0.7, Guild included only user specified glags. As of 0.7,
Guild includes all flags in default labels.

Let's run the `op.py` script without setting any flags.

    >> run("op.py")

The default label includes the flag values, regardless if we set or
change them.

    >> print_last_run()
    op.py  b=yes f=2.0 i=1 s=hello

Let's specify a single flag value.

    >> run("op.py", i=2)

    >> print_last_run()
    op.py  b=yes f=2.0 i=2 s=hello

And specify all flags:

    >> run("op.py", i=2, f=3.0, b=False, s="hi")

    >> print_last_run()
    op.py  b=no f=3.0 i=2 s=hi

## Explicit labels

When a label is provided by the user, it is always used, regardless of
flag values.

    >> run("op.py", label="custom label", i=2)

    >> print_last_run()
    op.py  custom label

We can include a reference to the flag value in the label.

    >> run("op.py", label="i equals ${i}", i=2)

    >> print_last_run()
    op.py  i equals 2

The special reference `${default_label` refers to the default label.

    >> run("op.py", label="${default_label}", i=1, s="hi")

    >> print_last_run()
    op.py  b=yes f=2.0 i=1 s=hi

    >> run("op.py", label="prefix ${default_label} suffix", i=2, s="bye")

    >> print_last_run()
    op.py  prefix b=yes f=2.0 i=2 s=bye suffix

## Label functions

    >> run("op.py", label="foo/bar.txt|basename")

    >> print_last_run()

## Tags

Tags are short-hand for a label `TAG ${default_label}`.

    >> run("op.py", tag="green", s="color", b=True)

    >> print_last_run()
    op.py  green b=yes f=2.0 i=1 s=color

## Operation defined labels

If a label is defined for an operation, it is used by default if one
is not specified by the user.

We'll use the `op` operation, defined in the project Guild file, which
defines a label.

    >> gf = guildfile.for_dir(sample("projects", "labels"))

    >> gf.default_model["op"].label
    'i:${i}, f:${f}, b:${b}, s:${s}'

Let's run this operation without specifying flags.

    >> run("op")

    >> print_last_run()
    op  i:1, f:2.0, b:yes, s:hello

When we provide flag values, the label format isn't changed - but the
values do.

    >> run("op", i=2, s="yo")

    >> print_last_run()
    op  i:2, f:2.0, b:yes, s:yo

## Labels and restarts

Labels are updated with new flag values when a run is restarted.

Here's run for `op`:

    >> run("op", i=4)

    >> print_last_run()
    op  i:4, f:2.0, b:yes, s:hello

Note the custom label format, which is taken from the opdef.

Let's restart the run with new flag values.

    >> last_run = project.list_runs()[0]

    >> run(restart=last_run.id, s="yello")

And the label:

    >> print_last_run()
    op  i:4, f:2.0, b:yes, s:yello

Guild saves the label template in the `op` attribute.

    >> last_run.get("op").get("label-template")
    'i:${i}, f:${f}, b:${b}, s:${s}'

Next we'll restart the run with a different label template.

    >> run(restart=last_run.id, i=6, s="whoop", label="${s}-${i}")

And the label:

    >> print_last_run()
    op  whoop-6

Guild has updated the label template.

    >> last_run.get("op").get("label-template")
    '${s}-${i}'

The new label template is now associated with the run.

    >> run(restart=last_run.id, i=7)

    >> print_last_run()
    op  whoop-7

## Trial labels

When an operation is run as a batch trial, the same rules apply as
described above.

Let's run `op.py` in a batch to generate two trials:

    >> run("op.py", i=[1,2], s="yello")

Let's list the last three runs, which include the batch and the two
trials:

    >> print_runs(3)
    op.py   b=yes f=2.0 i=2 s=yello
    op.py   b=yes f=2.0 i=1 s=yello
    op.py+

Here's the same result running `op`:

    >> run("op", i=[1,2], s="yello", b=False)

    >> print_runs(3)
    op   i:2, f:2.0, b:no, s:yello
    op   i:1, f:2.0, b:no, s:yello
    op+

In this case, we specify an explicit label for the trials:

    >> run("op", i=[1,2], label="i is ${i}")

    >> print_runs(3)
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

    >> run("op.py", i=[], opt_flags={"foo": 123})

    >> print_last_run()
    op.py+  foo=123

We can alternatively specify an explicit batch label:

    >> run("op.py", i=[], opt_flags={"foo": 123}, batch_label="empty batch")

    >> print_last_run()
    op.py+  empty batch

The special value `${default_label}` can be used in batch labels.

    >> run("op.py", i=[], opt_flags={"foo": 123}, batch_label="${default_label}")

    >> print_last_run()
    op.py+  foo=123


Use `batch_tag` for batch tags:

    >> run("op.py", i=[], opt_flags={"foo": 456}, batch_tag="bar")

    >> print_last_run()
    op.py+  bar foo=456

## Edge cases

Quoted numbers:

    >> run("op.py", i="1")

    >> print_last_run()
    op.py  b=yes f=2.0 i='1' s=hello

Values containing spaces:

    >> run("op.py", s="hello there")

    >> print_last_run()
    op.py  b=yes f=2.0 i=1 s='hello there'
