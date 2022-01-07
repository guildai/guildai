# Steps - Inherited Params

These tests illustrate the behavior of run steps (pipeline) run params
that are inherited by each step run.

We use the `steps` sample project.

    >>> project = Project(sample("projects", "steps"))

The `m5` model provides simple operations 'step' and 'op' that we can
use in our tests.

## Running Directly

Run steps without args. This uses the default label for the op run.

    >>> project.run("m5:steps")
    INFO: [guild] running op: m5:op
    hi from op

    >>> project.print_runs(labels=True, tags=True)
    m5:op     msg='hi from op'
    m5:steps

Run steps with a label. The label is passed through to the op run.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", label="label one")
    INFO: [guild] running op: m5:op --label label one
    hi from op

    >>> project.print_runs(labels=True, tags=True)
    m5:op     label one
    m5:steps  label one

Run steps with tags. Tags are also passed through to the op run.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", tags=("red", "blue"))
    INFO: [guild] running op: m5:op --tag red --tag blue
    hi from op

    >>> project.print_runs(labels=True, tags=True)
    m5:op     red blue msg='hi from op'  blue red
    m5:steps  red blue                   blue red

Specify both label and tags.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", label="label two", tags=("yellow", "green"))
    INFO: [guild] running op: m5:op --label label two --tag yellow --tag green
    hi from op

    >>> project.print_runs(labels=True, tags=True)
    m5:op     label two  green yellow
    m5:steps  label two  green yellow

## Stage and Start

Staging and then starting a steps (pipeline) operation shows the same
behavior after the start.

Stage steps without args.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", stage=True)
    m5:steps staged as ...
    To start the operation, use 'guild run --start ...'

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:steps      staged

    >>> project.run(start=project.list_runs()[0].id)
    INFO: [guild] running op: m5:op
    hi from op

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:op     msg='hi from op'    completed
    m5:steps                      completed

Stage steps with a label. The label is used when the op is later
started.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", label="label three", stage=True)
    m5:steps staged as ...
    To start the operation, use 'guild run --start ...'

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:steps  label three    staged

    >>> project.run(start=project.list_runs()[0].id)
    INFO: [guild] running op: m5:op --label label three
    hi from op

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:op     label three    completed
    m5:steps  label three    completed

Stage steps with tags.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", tags=("dog", "cat"), stage=True)
    m5:steps staged as ...
    To start the operation, use 'guild run --start ...'

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:steps  dog cat   cat dog  staged

    >>> project.run(start=project.list_runs()[0].id)
    INFO: [guild] running op: m5:op --tag dog --tag cat
    hi from op

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:op     dog cat msg='hi from op'  cat dog  completed
    m5:steps  dog cat                   cat dog  completed

Stage with both label and tags.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", label="label four", tags=("bird", "mouse"), stage=True)
    m5:steps staged as ...
    To start the operation, use 'guild run --start ...'

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:steps  label four  bird mouse  staged

    >>> project.run(start=project.list_runs()[0].id)
    INFO: [guild] running op: m5:op --label label four --tag bird --tag mouse
    hi from op

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:op     label four  bird mouse  completed
    m5:steps  label four  bird mouse  completed

Stage with label and tags and override both on start.

    >>> project.delete_runs()
    Deleted 2 run(s)

    >>> project.run("m5:steps", label="label four", tags=("bird", "mouse"), stage=True)
    m5:steps staged as ...
    To start the operation, use 'guild run --start ...'

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:steps  label four  bird mouse  staged

    >>> project.run(start=project.list_runs()[0].id, label="label five", tags=("cat", "dog"))
    INFO: [guild] running op: m5:op --label label five --tag cat --tag dog
    hi from op

    >>> project.print_runs(labels=True, tags=True, status=True)
    m5:op     label five  cat dog  completed
    m5:steps  label five  cat dog  completed
