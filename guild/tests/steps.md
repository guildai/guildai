# Operation steps

Operations may be defined using a sequence of steps, rather than a
main or exec spec.

We'll use the sample project 'steps' to illustrate the behavior.

    >>> use_project("steps")

The project defines several operations under 'models' (operation
namespaces):

    >>> run("guild models")
    m1
    m2
    m3
    m4
    m5
    m6

## Basic steps

Steps are stored as the operation `steps` attribute. They are not
processed by the Guild file. Ghey are passed through to
`guild.steps_main` as unprocessed data. Validation is performed by
`steps_main` during the operation. This is a less-than-ideal
arrangement but offers the advantage of moving the steps logic out of
Guild core and into a workflow specific main module.

We can examine the definition of `steps` for one of the project
operations.

    >>> gf = guildfile.for_dir(".")

    >>> gf.models["m1"]["steps-basic"].steps
    ['step-1', 'step-2']

Note that the raw data structure (Python list) is provided rather than
any higher level structured data.

The `steps-basic` operation runs the two operations in the order
specified.

    >>> run("guild run m1:steps-basic -y")
    INFO: [guild] running step-1: m1:step-1
    hello step-1
    INFO: [guild] running step-2: m1:step-2
    hello step-2

In this case, three runs are generated.

    >>> run("guild runs -s")
    [1]  m1:step-2       completed
    [2]  m1:step-1       completed
    [3]  m1:steps-basic  completed

In running `steps-basic`, Guild generates runs for `step-1` and
`step-2`.

Each run generated by a step is a normal Guild run.

Files generated for the steps:

    >>> run("guild ls 1 -n")
    fail.py
    guild.yml
    loss.py
    step-2
    step.py

    >>> run("guild ls 2 -n")
    fail.py
    guild.yml
    loss.py
    step-1
    step.py

The parent run `m1:steps-basic` contain symbolic links to the child
runs.

Contents of the parent run:

    >>> run("guild ls 3 -n")
    step-1/
    step-2/

Get the targets of the two links under parent:

    >>> parent_dir = run_capture("guild select 3 --path")
    >>> step_1_link_target = realpath(path(parent_dir, "step-1"))
    >>> step_2_link_target = realpath(path(parent_dir, "step-2"))

Get the two step directories:

    >>> step_1_path = run_capture("guild select 2 --path")
    >>> step_2_path = run_capture("guild select 1 --path")

Verify that the links point to the step runs:

    >>> step_1_link_target == step_1_path
    True

    >>> step_2_link_target == step_2_path
    True

## Named steps

Steps can be named, which specifies the name of the link to
create. Names are also used when referring to the step.

The `steps-named` operation shows how names are used.

    >>> run("guild run m1:steps-named -y")
    INFO: [guild] running s1: m1:step-1
    hello step-1
    INFO: [guild] running s2: m1:step-2
    hello step-2

    >>> run("guild runs -s -n3")
    [1]  m1:step-2       completed
    [2]  m1:step-1       completed
    [3]  m1:steps-named  completed

The links generated in the stepped run use the step names.

    >>> run("guild ls 3 -n")
    s1/
    s2/

The stepped run `steps-basic` contains symbolic links to the two
genated runs.

Get the targets of the two step runs:

    >>> parent_dir = run_capture("guild select 3 --path")
    >>> s1_link_target = realpath(path(parent_dir, "s1"))
    >>> s2_link_target = realpath(path(parent_dir, "s2"))

Get the two step directories:

    >>> s1_path = run_capture("guild select 2 --path")
    >>> s2_path = run_capture("guild select 1 --path")

Verify that the links point to the step runs:

    >>> s1_link_target == s1_path
    True

    >>> s2_link_target == s2_path
    True

## Repeated steps

If a step is run more than once, the link names for subsequent runs
use an incrementing suffix to avoid name collisions.

    >>> run("guild run m1:steps-repeat -y")
    INFO: [guild] running step-1: m1:step-1
    hello step-1
    INFO: [guild] running step-1: m1:step-1
    hello step-1
    INFO: [guild] running step-1: m1:step-1
    hello step-1

    >>> run("guild runs -s -n4")
    [1]  m1:step-1        completed
    [2]  m1:step-1        completed
    [3]  m1:step-1        completed
    [4]  m1:steps-repeat  completed

    >>> run("guild ls 4 -n")
    step-1/
    step-1_2/
    step-1_3/

As with the previous examples, the links reference the step runs.

Get the targets of the two step runs:

    >>> parent_dir = run_capture("guild select 4 --path")
    >>> step_1_link_target = realpath(path(parent_dir, "step-1"))
    >>> step_1_2_link_target = realpath(path(parent_dir, "step-1_2"))
    >>> step_1_3_link_target = realpath(path(parent_dir, "step-1_3"))

Get the three step directories:

    >>> step_1_path = run_capture("guild select 3 --path")
    >>> step_1_2_path = run_capture("guild select 2 --path")
    >>> step_1_3_path = run_capture("guild select 1 --path")

Verify that the links point to the step runs:

    >>> step_1_link_target == step_1_path
    True

    >>> step_1_2_link_target == step_1_2_path
    True

    >>> step_1_3_link_target == step_1_3_path
    True

## Stepped operations and flags

Stepped operations may contain flags like any other operation. In the
case of a stepped operation, however, flags are used as arguments to
the operations they run.

We illustrate using `hello`, which is an operation that prints a
message specified with the `msg` flag. `msg` defaults to 'hello
world'.

    >>> run("guild run m1:hello -y")
    hello world

    >>> run("guild run m1:hello msg='hello from test' -y")
    hello from test

`steps-hello` is a stepped operation that runs `hello` twice. It
defines its own flag `msg`, which defaults to 'hello steps', and
passes that flag value through to its steps.

    >>> run("guild run m1:steps-hello -y")
    INFO: [guild] running hello: m1:hello msg='hello steps'
    hello steps
    INFO: [guild] running hello: m1:hello msg='hello steps (again)'
    hello steps (again)

    >>> run("guild run m1:steps-hello msg='hello from test 2' -y")
    INFO: [guild] running hello: m1:hello msg='hello from test 2'
    hello from test 2
    INFO: [guild] running hello: m1:hello msg='hello from test 2 (again)'
    hello from test 2 (again)

## Running operations across models

A stepped operation may run operations defined in other models. Model
`m2` illustrates this with the `composite` operation.

    >>> run("guild run m2:composite -y")
    INFO: [guild] running hello: m2:hello msg='hello m2, from composite'
    hello m2, from composite
    INFO: [guild] running m1:hello: m1:hello msg='hello m1, from composite'
    hello m1, from composite

The operation accepts a `name` flag, which change the messages used
with `hello`.

    >>> run("guild run m2:composite name=test -y")
    INFO: [guild] running hello: m2:hello msg='hello m2, from test'
    hello m2, from test
    INFO: [guild] running m1:hello: m1:hello msg='hello m1, from test'
    hello m1, from test

## Invalid steps

Step config is validated while running the stepped operation. Invalid
step configuration will cause the parent operation to fail with an
error.

The `m3` model contains various operations that have invalid step
configuration.

    >>> run("guild run m3:steps-invalid-bad-opspec-1 -y")
    guild: invalid step data: [1, 2, 3]
    <exit 1>

    >>> run("guild run m3:steps-invalid-bad-opspec-2 -y")
    guild: invalid step data: None
    <exit 1>

    >>> run("guild run m3:steps-invalid-bad-opspec-3 -y")
    guild: invalid step {'run': '   '}: must define run
    <exit 1>

    >>> run("guild run m3:steps-invalid-bad-opspec-4 -y")
    guild: invalid step {}: must define run
    <exit 1>

    >>> run("guild run m3:steps-invalid-bad-op -y")
    INFO: [guild] running not-defined: m3:not-defined
    guild: operation 'not-defined' is not defined for model 'm3'
    Try 'guild operations m3' for a list of available operations.
    <exit 1>

Steps do not support additional run options. Any provided causes Guild
to print a warning message.

    >>> run("guild run m3:ignored-params -y")
    WARNING: [guild] run parameter run_dir used in 'm1:hello --run-dir /tmp --stage' ignored
    WARNING: [guild] run parameter stage used in 'm1:hello --run-dir /tmp --stage' ignored
    INFO: [guild] running m1:hello: m1:hello
    hello world

## Steps and scalars

The scalar values generated by step operations are available under the
top-level operation via the run index.

We use the operations in the `m4` model to illustate.

First we delete our current runs.

    >>> run("guild runs rm -y")
    Deleted 31 run(s)

`m4:end-to-end` runs the sequence `prepare`, `train`, and
`evaluate`. This simulates a common end-to-end training and evaluation
scenario

    >>> run("guild run m4:end-to-end -y")  # doctest: +REPORT_UDIFF
    INFO: [guild] running prepare: m4:prepare --needed
    prepared data
    INFO: [guild] running train: m4:train loss=1.0
    Resolving operation:prepare
    Using run ... for operation:prepare
    loss=1.0
    INFO: [guild] running eval: m4:evaluate acc=0.5
    Resolving operation:prepare
    Using run ... for operation:prepare
    Resolving operation:train
    Using run ... for operation:train
    acc=0.5

The generated runs:

    >>> run("guild runs -s")
    [1]  m4:evaluate    completed  acc=0.5 operation:prepare=... operation:train=...
    [2]  m4:train       completed  loss=1.0 operation:prepare=...
    [3]  m4:prepare     completed
    [4]  m4:end-to-end  completed  acc=0.5 loss=1.0

Files associated with each run:

    >>> run("guild ls -n 4")
    eval/
    prepare/
    train/

    >>> run("guild ls -n 3")
    data
    fail.py
    guild.yml
    loss.py
    step.py

    >>> run("guild ls -n 2")
    data
    fail.py
    guild.yml
    loss.py
    model
    step.py

    >>> run("guild ls -n 1")
    data
    fail.py
    guild.yml
    loss.py
    model
    step.py

Compare runs:

    >>> run("guild compare -t -cc .operation,.status,.label,#acc,#loss")  # doctest: -WINDOWS
    run  operation      status     label                                              acc  loss
    ...  m4:evaluate    completed  acc=0.5 operation:prepare=... operation:train=...  0.5
    ...  m4:train       completed  loss=1.0 operation:prepare=...                          1.0
    ...  m4:prepare     completed
    ...  m4:end-to-end  completed  acc=0.5 loss=1.0                                   0.5  1.0

Note that `end-to-end` reflects the `loss` and `acc` of its steps.

BUG: On Windows, stepped runs do not roll up from their steps due to a
bug in Python symlink traversal, which is reflected in the TensorBoard
tfevent generator. This behavior is passed through to Guild as Guild
uses TensorBoard to read TF event files.

    >>> run("guild compare -t -cc .operation,.status,.label,#acc,#loss")  # doctest: +WINDOWS_ONLY
    run  operation      status     label                                              acc  loss
    ...  m4:evaluate    completed  acc=0.5 operation:prepare=... operation:train=...  0.5
    ...  m4:train       completed  loss=1.0 operation:prepare=...                          1.0
    ...  m4:prepare     completed
    ...  m4:end-to-end  completed  acc=0.5 loss=1.0

## Steps and --force-flags

There's currently no way to specify a step operation flag when running
a stepped operation. The stepped operation must explicitly pass
through its flags to steps. This is inconvenient for users who want to
change step operation flags as they have to modify the Guild file.

This will be changed in time so that users can specify operation flags
when running a stepped operation.

E.g.

    $ guild run m5:steps op:msg=hello

However, this is not yet supported.

As a workaround, a user can specify `--force-flags` to force any
non-stepped flags to be passed through to step operations.

We'll use the `m5` model to illustrate.

`m5:steps` without flags:

    >>> run("guild run m5:steps -y")
    INFO: [guild] running op: m5:op
    hi from op

When we specify flags that are not explicitly supported by the parent
operation, we get an error.

    >>> run("guild run m5:steps msg='hi from test' -y")
    guild: unsupported flag 'msg'
    Try 'guild run m5:steps --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

    >>> run("guild run m5:steps op:msg='hi from test' -y")
    guild: unsupported flag 'op:msg'
    Try 'guild run m5:steps --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

When we use `--force-flags`, Guild passes the otherwise unsupported
flag values through. In this case, we need to qualify the flag name
with the operation.

    >>> run("guild run m5:steps op:msg='hi from test 2' --force-flags -y")
    INFO: [guild] running op: m5:op msg='hi from test 2'
    hi from test 2

The model may optionally be included in the flag value.

    >>> run("guild run m5:steps m5:op:msg='hi from test 3' --force-flags -y")
    INFO: [guild] running op: m5:op msg='hi from test 3'
    hi from test 3

When both variants are provided, the more complete spec is used.

    >>> run("guild run m5:steps op:msg=hi-4 m5:op:msg=hi-5 --force-flags -y")
    INFO: [guild] running op: m5:op msg=hi-5
    hi-5

## Steps and labels

Labels specified with `--label` are applied to the parent and the step
runs.

    >>> run("guild run m2:composite --label='a label' -y")
    INFO: [guild] running hello: m2:hello --label a label msg='hello m2, from composite'
    hello m2, from composite
    INFO: [guild] running m1:hello: m1:hello --label a label msg='hello m1, from composite'
    hello m1, from composite

    >>> run("guild runs -s -n3")
    [1]  m1:hello      completed  a label
    [2]  m2:hello      completed  a label
    [3]  m2:composite  completed  a label

The same is true for `--tag`.

    >>> run("guild run m2:composite -t blue -t green -y")
    INFO: [guild] running hello: m2:hello --tag blue --tag green msg='hello m2, from composite'
    hello m2, from composite
    INFO: [guild] running m1:hello: m1:hello --tag blue --tag green msg='hello m1, from composite'
    hello m1, from composite

    >>> run("guild runs -s -n3")
    [1]  m1:hello      completed  blue green msg='hello m1, from composite'
    [2]  m2:hello      completed  blue green msg='hello m2, from composite'
    [3]  m2:composite  completed  blue green name=composite
