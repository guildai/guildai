# Filter runs command impl

These tests demonstrate how the `--filter` option works when running
Guild commands.

Tests use the `filter` project.

    >>> use_project("filter")

The operations we'll be running:

    >>> run("guild run fixed:train --help-op")
    ???
    Flags:
      batch  (default is 100)
      lr     (default is 0.1)
      seed   (default is 1)

    >>> run("guild run fixed:test --help-op")
    ???
    Flags:
      seed  (default is 1)

Generate run training runs using `fixed:train` and `fixed:test`. This
gives us predictable results given a seed.

    >>> run("guild run fixed:train lr=[0.01,0.1] seed=[1,2] -y")
    INFO: [guild] Running trial ...: fixed:train (batch=100, lr=0.01, seed=1)
    loss: 1
    acc: 95
    INFO: [guild] Running trial ...: fixed:train (batch=100, lr=0.01, seed=2)
    loss: 2
    acc: 83
    INFO: [guild] Running trial ...: fixed:train (batch=100, lr=0.1, seed=1)
    loss: 1
    acc: 95
    INFO: [guild] Running trial ...: fixed:train (batch=100, lr=0.1, seed=2)
    loss: 2
    acc: 83

    >>> run("guild run fixed:test seed=[2,3] -y")
    INFO: [guild] Running trial ...: fixed:test (operation:train=..., seed=2)
    INFO: [guild] Resolving operation:train
    INFO: [guild] Using run ... for operation:train
    test-acc: 50
    INFO: [guild] Running trial ...: fixed:test (operation:train=..., seed=3)
    INFO: [guild] Resolving operation:train
    INFO: [guild] Using run ... for operation:train
    test-acc: 84

Run an operation that will fail (we use the error status below for
filtering).

    >>> run("guild run fail --label oops -y")
    Oops!
    <exit 1>

List the runs.

    >>> run("guild runs -s")
    [1]  fail         error      oops
    [2]  fixed:test   completed  operation:train=... seed=3
    [3]  fixed:test   completed  operation:train=... seed=2
    [4]  fixed:train  completed  batch=100 lr=0.1 seed=2
    [5]  fixed:train  completed  batch=100 lr=0.1 seed=1
    [6]  fixed:train  completed  batch=100 lr=0.01 seed=2
    [7]  fixed:train  completed  batch=100 lr=0.01 seed=1

Use the compare command to show scalar values. We filter on these
values below.

    >>> run("guild compare -t -cc .operation,=batch,=lr,=seed,loss,acc,test-acc")
    run  operation    batch  lr    seed  loss  acc    test-acc
    ...  fail
    ...  fixed:test                3                  84.0
    ...  fixed:test                2                  50.0
    ...  fixed:train  100    0.1   2     2.0   83.0
    ...  fixed:train  100    0.1   1     1.0   95.0
    ...  fixed:train  100    0.01  2     2.0   83.0
    ...  fixed:train  100    0.01  1     1.0   95.0
    <exit 0>

Helper function to show filtered runs:

    >>> def filter(expr, cols=""):
    ...     run(f"guild compare -t -cc .operation,{cols or '.label'} "
    ...         f"--filter {shlex_quote(expr)}")

List runs using various filters:

    >>> filter("true")
    run  operation    label
    ...  fail
    ...  fixed:test   operation:train=... seed=3
    ...  fixed:test   operation:train=... seed=2
    ...  fixed:train  batch=100 lr=0.1 seed=2
    ...  fixed:train  batch=100 lr=0.1 seed=1
    ...  fixed:train  batch=100 lr=0.01 seed=2
    ...  fixed:train  batch=100 lr=0.01 seed=1

    >>> filter("false")
    <exit 0>

    >>> filter("op = test")
    run  operation   label
    ...  fixed:test  operation:train=... seed=3
    ...  fixed:test  operation:train=... seed=2

    >>> filter("op = test and seed = 3")
    run  operation   label
    ...  fixed:test  operation:train=... seed=3

    >>> filter("op = train and seed in [1,3] and lr > 0.01 and lr < 0.2")
    run  operation    label
    ...  fixed:train  batch=100 lr=0.1 seed=1

    >>> filter(
    ...     "(operation = fixed:train and lr = 0.1 and loss < 2) "
    ...     "or (op = test and test-acc > 80)",
    ...     "=lr,loss,test-acc"
    ... )
    run  operation    lr   loss  test-acc
    ...  fixed:test              84.0
    ...  fixed:train  0.1  1.0

    >>> filter("model = ''")
    run  operation  label
    ...  fail       oops

    >>> filter("acc is undefined", "acc")
    run  operation   acc
    ...  fail
    ...  fixed:test
    ...  fixed:test

    >>> filter("acc is not undefined", "acc")
    run  operation    acc
    ...  fixed:train  83.0
    ...  fixed:train  95.0
    ...  fixed:train  83.0
    ...  fixed:train  95.0

    >>> filter("label contains oop")
    run  operation  label
    ...  fail       oops

    >>> filter("label = oops")
    run  operation  label
    ...  fail       oops

    >>> filter("label not contains batch")
    run  operation   label
    ...  fail        oops
    ...  fixed:test  operation:train=... seed=3
    ...  fixed:test  operation:train=... seed=2

The 'op' attribute is just the operation name, not the model.

    >>> filter("op = fixed:train")
    <exit 0>

Syntax errors:

    >>> filter("foo = (")
    guild: syntax error in filter at position 6: unexpected token '('
    <exit 1>

    >>> filter("(")
    guild: syntax error in filter - unexpected end of expresion
    <exit 1>
