# Compare Columns

The `compare` project illustrates various compare features.

    >>> project = Project(sample("projects/compare"))

## Default compare columns

By default all of the flags and scalars are used in compare.

Here's a run of the script, which has no compare info:

    >>> project.run("op1.py")
    x: 2
    y: 4
    z/ab: 3
    sys/x: 123

Here's the default compare output:

    >>> project.compare()
    [['run', 'operation', 'started', 'time', 'status', 'label', 'a', 'b', 'step', 'x', 'y', 'z/ab'],
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', 1, 2, 0, 2.0, 4.0, 3.0]]


Compare with extra cols, which includes source code digest:

    >>> project.compare(extra_cols=True)
    [['run', 'operation', 'started', 'time', 'status', 'label', 'sourcecode', 'a', 'b', 'step', 'x', 'y', 'z/ab'],
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', '8ae8b71b', 1, 2, 0, 2.0, 4.0, 3.0]]

Include all scalars:

    >>> project.compare(all_scalars=True)
    [['run', 'operation', 'started', 'time', 'status', 'label', 'a', 'b', 'step', 'sys/x', 'x', 'y', 'z/ab'],
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', 1, 2, 0, 123.0, 2.0, 4.0, 3.0]]

## Explicit compare columns

The project Guild file defines explicit compare cols for the `op1` operation.

    >>> from guild import guildfile
    >>> gf = guildfile.for_dir(project.cwd)

    >>> op1 = gf.default_model.operations[0]
    >>> op1.name
    'op1'

    >>> op1.compare
    ['=a as A', '=b as B', 'x step as x_step', 'x', 'y', 'z/ab as ab']

Let's run the operation:

    >>> project.run("op1", flags={"a": 2, "b": 3})
    x: 3
    y: 5
    z/ab: 5
    sys/x: 123

And compare the runs:

    >>> project.compare(extra_cols=True)
    [['run', 'operation', 'started', 'time', 'status', 'label', 'sourcecode', 'A', 'B', 'x_step', 'x', 'y', 'ab', 'a', 'b', 'step', 'z/ab'],
     ['...', 'op1', '...', '...', 'completed', 'a=2 b=3', '8ae8b71b', 2, 3, 0, 3.0, 5.0, 5.0, None, None, None, None],
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', '8ae8b71b', None, None, None, 2.0, 4.0, None, 1, 2, 0, 3.0]]

## Comparing columns containing diverse value types

Reset the project:

    >>> project = Project(sample("projects/compare"))

Generate runs with a diverse range of values types for flag `a`:

    >>> project.run("op2.py")
    None

    >>> project.run("op2.py", flags={"x": 1})
    1

    >>> project.run("op2.py", flags={"x": 1.123})
    1.123

    >>> project.run("op2.py", flags={"x": "hello"})
    hello

    >>> project.run("op2.py", flags={"x": ""})

    >>> project.run("op2.py", flags={"x": None})
    None

Compare, sorting by min `x`:

    >>> project.compare(cols="x", skip_core=True, min_col="x")
    [['run', 'x'],
     ['...', ''],
     ['...', 1],
     ['...', 1.123],
     ['...', 'hello'],
     ['...', None],
     ['...', None]]

Compare, sorting by max `x`:

    >>> project.compare(cols="x", skip_core=True, max_col="x")
    [['run', 'x'],
     ['...', 'hello'],
     ['...', 1.123],
     ['...', 1],
     ['...', ''],
     ['...', None],
     ['...', None]]

Note that `None` values appear at the bottom in both cases.

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
