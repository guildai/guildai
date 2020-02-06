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
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', '58738be9', 1, 2, 0, 2.0, 4.0, 3.0]]

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
     ['...', 'op1', '...', '...', 'completed', 'a=2 b=3', '58738be9', 2, 3, 0, 3.0, 5.0, 5.0, None, None, None, None],
     ['...', 'op1.py', '...', '...', 'completed', 'a=1 b=2', '58738be9', None, None, None, 2.0, 4.0, None, 1, 2, 0, 3.0]]
