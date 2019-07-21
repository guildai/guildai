# Custom Scalars examples

The example in `custom-scalars` can be used to illustrate both the
default scalar capture mechanism and custom scalars.

    >>> cd("examples/custom-scalars")

## train.py

Default scalars captured when running `train.py` as a script:

    >>> run("guild run train.py -y", ignore="Refreshing")
    step: 1
    loss: 2.345
    accuracy: 0.123
    <BLANKLINE>
    step: 2
    loss: 1.234
    accuracy: 0.456
    <exit 0>

    >>> run("guild runs info --scalars")
    id: ...
    scalars:
      accuracy: 0.456000 (step 2)
      loss: 1.234000 (step 2)
    <exit 0>

We can use the `--test-output-scalars` option of the `run` command to
test custom output scalar patterns against sample script output.

    >>> run("echo 'foo: 1.123' | guild run train.py --test-output-scalars -")
    foo: 1.123
      '^([^ \t]+):\\s+([[0-9\\.e\\-]+)$': [('foo', '1.123')] (foo=1.123)
    <exit 0>

    >>> run("echo 'bar' | guild run train.py --test-output-scalars -")
    bar
      '^([^ \t]+):\\s+([[0-9\\.e\\-]+)$': <no match>
    <exit 0>

## train

The project defines two operations:

    >>> run("guild ops -p .")
    train
    train2
    <exit 0>

`train` defines a different set of scalars to capture.

Let's run it to see what's generated:

    >>> run("guild run train -y")
    step: 1
    loss: 2.345
    accuracy: 0.123
    <BLANKLINE>
    step: 2
    loss: 1.234
    accuracy: 0.456
    <exit 0>

    >>> run("guild runs info --scalars")
    id: ...
    scalars:
      accuracy: 0.456000 (step 2)
      loss: 1.234000 (step 2)
    <exit 0>

When we test a general `NAME: VAL` pattern for the `train` operation,
we don't match unless `NAME` is either `loss`, `accuracy`, or `step`:

    >>> run("""guild run train --test-output-scalars - << EOF
    ... step: 1
    ... loss: 1.1
    ... accuracy: 0.22
    ... foo: 2.2
    ... bar 3.3
    ... faz
    ... EOF""")
    step: 1
      'accuracy: ([0-9\\.e\\-]+)': <no match>
      'loss: ([0-9\\.e\\-]+)': <no match>
      'step: ([0-9\\.e\\-]+)': [('1',)] (step=1.0)
    loss: 1.1
      'accuracy: ([0-9\\.e\\-]+)': <no match>
      'loss: ([0-9\\.e\\-]+)': [('1.1',)] (loss=1.1)
      'step: ([0-9\\.e\\-]+)': <no match>
    accuracy: 0.22
      'accuracy: ([0-9\\.e\\-]+)': [('0.22',)] (accuracy=0.22)
      'loss: ([0-9\\.e\\-]+)': <no match>
      'step: ([0-9\\.e\\-]+)': <no match>
    foo: 2.2
      'accuracy: ([0-9\\.e\\-]+)': <no match>
      'loss: ([0-9\\.e\\-]+)': <no match>
      'step: ([0-9\\.e\\-]+)': <no match>
    bar 3.3
      'accuracy: ([0-9\\.e\\-]+)': <no match>
      'loss: ([0-9\\.e\\-]+)': <no match>
      'step: ([0-9\\.e\\-]+)': <no match>
    faz
      'accuracy: ([0-9\\.e\\-]+)': <no match>
      'loss: ([0-9\\.e\\-]+)': <no match>
      'step: ([0-9\\.e\\-]+)': <no match>
    <exit 0>
