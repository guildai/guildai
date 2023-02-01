# Compare Columns

The `compare` project illustrates various compare features.

    >>> use_project("compare")

## Default compare columns

By default all of the flags and scalars are used in compare.

Run the script `op1.py`, which has no additional compare
configuration.

    >>> run("guild run op1.py -y")
    x: 2
    y: 4
    z/ab: 3
    sys/x: 123

Show the run with the `compare` command.

    >>> run("guild compare -t")
    run  operation  started  time     status     label    a  b  step  x    y    z/ab
    ...  op1.py     ...      ...      completed  a=1 b=2  1  2  0     2.0  4.0  3.0

Use the `api` command to generate parseable JSON with the compare data.

    >>> pprint(json.loads(run_capture("guild api compare")))
    [['id',
      'operation',
      'started',
      'time',
      'status',
      'label',
      'a',
      'b',
      'step',
      'x',
      'y',
      'z/ab'],
     ['...',
      'op1.py',
      '...',
      '...',
      'completed',
      'a=1 b=2',
      1,
      2,
      0,
      2.0,
      4.0,
      3.0]]

Show extra columns. This shows the `sourcecode` digest for the runs.

    >>> run("guild compare -t --extra-cols")
    run  operation  started  time  status     label    sourcecode  a  b  step  x    y    z/ab
    ...  op1.py     ...      ...   completed  a=1 b=2  8ae8b71b    1  2  0     2.0  4.0  3.0

Show all scalars.

    >>> run("guild compare -t --all-scalars")
    run  operation  started  time  status     label    a  b  step  sys/x  x    y    z/ab
    ...  op1.py     ...      ...   completed  a=1 b=2  1  2  0     123.0  2.0  4.0  3.0

## Explicit compare columns

The project Guild file defines explicit compare cols for the `op1` operation.

    >>> gf = guildfile.for_dir(".")
    >>> op1 = gf.default_model.operations[0]

    >>> op1.name
    'op1'

    >>> op1.compare
    ['=a as A', '=b as B', 'x step as x_step', 'x', 'y', 'z/ab as ab']

Run the operation.

    >>> run("guild run op1 a=2 b=3 -y")
    x: 3
    y: 5
    z/ab: 5
    sys/x: 123

Compare the runs.

    >>> run("guild compare -t")
    run  operation  started  time  status     label    A  B  x_step  x    y    ab   a  b  step  z/ab
    ...  op1        ...      ...   completed  a=2 b=3  2  3  0       3.0  5.0  5.0
    ...  op1.py     ...      ...   completed  a=1 b=2                2.0  4.0       1  2  0     3.0

    >>> pprint(json.loads(run_capture("guild api compare")))
    [['id',
      'operation',
      'started',
      'time',
      'status',
      'label',
      'A',
      'B',
      'x_step',
      'x',
      'y',
      'ab',
      'a',
      'b',
      'step',
      'z/ab'],
     ['...',
      'op1',
      '...',
      '...',
      'completed',
      'a=2 b=3',
      2,
      3,
      0,
      3.0,
      5.0,
      5.0,
      None,
      None,
      None,
      None],
     ['...',
      'op1.py',
      '...',
      '...',
      'completed',
      'a=1 b=2',
      None,
      None,
      None,
      2.0,
      4.0,
      None,
      1,
      2,
      0,
      3.0]]

## Comparing columns containing diverse value types

Reset the project.

    >>> use_project("compare")

Generate runs with various value types for flag `a`.

    >>> run("guild run op2.py -y --run-id 1")
    None
    <exit 0>

    >>> run("guild run op2.py x=1 -y --run-id 2")
    1

    >>> run("guild run op2.py x=1.123 -y --run-id 3")
    1.123

    >>> run("guild run op2.py x=hello -y --run-id 4")
    hello

    >>> run("guild run op2.py x= -y --run-id 5")
    <exit 0>

    >>> run("guild run op2.py x=null -y --run-id 6")
    None

Compare, sorting by min `x`.

    >>> run("guild compare -t --skip-core --cols .label,x --min x")
    run  x      label
    5           x=''
    2    1      x=1
    3    1.123  x=1.123
    4    hello  x=hello
    6
    1

Compare, sorting by max `x`.

    >>> run("guild compare -t --skip-core --cols .label,x --max x")
    run  x      label
    4    hello  x=hello
    3    1.123  x=1.123
    2    1      x=1
    5           x=''
    6
    1

Note that runs where `x=None` (IDs `6` and `1`) appear at the bottom
in both cases.

### Sort keys

The clas `guild.commands.compare_impl._SortKey` is used as a universal
key across value types.

    >>> from guild.commands.compare_impl import _SortKey as K

Below are various examples.

When comparing `None` values, we can specify wither the unknown value
should be sorted at the bottom or the top by using `min` and `max`
respectively.

By default `None` is always less than except when compared to `None`.

    >>> K(None) < K(None)
    False

    >>> K(None, max=True) < K(None)
    False

    >>> K(None) < K(1)
    True

    >>> K(None) < K("a")
    True

We reverse this by setting `max` to `True`.

    >>> K(None, max=True) < K(1)
    False

    >>> K(None, max=True) < K("a")
    False

If values are the same type, they are compared directly:

    >>> K("") < K("")
    False

    >>> K("a") < K("b")
    True

    >>> K(2) < K(1)
    False

    >>> K(1) < K(2)
    True

Numeric values, including booleans, can be compared directly:

    >>> K(1.0) < K(2)
    True

    >>> K(1) < K(True)
    False

    >>> K(False) < K(1)
    True

Otherwise both values are coverted to strings and compared.

    >>> K(1) < K("1")
    False

    >>> K(1) < K("2")
    True

    >>> K(1) < K("02")
    False

## Skip unchanged cols

The `--skip-unchanged` option tells Guild to skip any columns
containing unchanged values -- i.e. that only contain the same value.

As a baseline, here's a comparison using some columns we might be
interested in.

    >>> run("guild compare --strict-cols .op,.status,.label,=x -t")
    run  op      status     label    x
    6    op2.py  completed
    5    op2.py  completed  x=''
    4    op2.py  completed  x=hello  hello
    3    op2.py  completed  x=1.123  1.123
    2    op2.py  completed  x=1      1
    1    op2.py  completed

Note `op` and `status` columns each have unchanged values. We can skip
these columns using `--skip-unchanged`.

    >>> run("guild compare --strict-cols .op,.status,.label,=x -t --skip-unchanged")
    run  label    x
    6
    5    x=''
    4    x=hello  hello
    3    x=1.123  1.123
    2    x=1      1
    1

Compare runs where `x` is `None` (runs `6` and `1`) using
`--skip-unchanged`. In this case, all specified columns are skipped
because they're the same.

    >>> run("guild compare --strict-cols .op,.status,.label,=x -t --skip-unchanged 1 6")
    run
    6
    1

## Run detail

Run detail is shown when the user presses Enter on a run in the
compare tabview. To illustrate, we call a private function in
`compare_impl` to format run details.

We need an index for the project runs.

    >>> from guild import index as indexlib
    >>> index = indexlib.RunIndex()

Refresh the index using the current runs.

    >>> from guild import var
    >>> runs = var.runs(sort=["-timestamp"])
    >>> index.refresh(runs)

Get the default callback function used to format run detail from
`compare_impl`.

    >>> from guild.commands.compare_impl import _format_run_detail

Show run detail for some runs.

    >>> print(_format_run_detail(runs[1], index))
    Id: 5
    Operation: op2.py
    From: .../samples/projects/compare
    Status: completed
    Started: ...
    Stopped: ...
    Time: 0:00:...
    Label: x=''
    Flags:
      x:

    >>> print(_format_run_detail(runs[3], index))
    Id: 3
    Operation: op2.py
    From: .../samples/projects/compare
    Status: completed
    Started: ...
    Stopped: ...
    Time: 0:00:...
    Label: x=1.123
    Flags:
      x: 1.123
