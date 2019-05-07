# Compare Columns

The `compare` project illustrates various compare features.

    >>> project = Project(sample("projects/compare"))

## Default compare columns

By default all of the flags and scalars are used in compare.

Here's a run of the script, which has no compare info:

    >>> project.run("op1.py")
    x: 2
    y: 4

Here's the default compare output:

    >>> project.compare()
    [['run', 'operation', 'started', 'time', 'status', 'label', 'a', 'b', 'step', 'x', 'y'],
     ['...', 'op1.py', '...', '...', 'completed', None, 1, 2, 0, 2.0, 4.0]]

## Explicit compare columns

The project Guild file defines explicit compare cols for the `op1` operation.

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(project.cwd)

    >>> op1 = gf.default_model.operations[0]
    >>> op1.name
    'op1'

    >>> op1.compare
    ['=a as A', '=b as B', 'x step as x_step', 'x', 'y']

Let's run the operation:

    >>> project.run("op1", flags=dict(a=2, b=3))
    x: 3
    y: 5

And compare the runs:

    >>> project.compare()
    [['run', 'operation', 'started', 'time', 'status', 'label', 'A', 'B', 'x_step',
      'x', 'y', 'a', 'b', 'step'],
     ['...', 'op1', '...', '...', 'completed', None, 2, 3, 0, 3.0, 5.0, None, None, None],
     ['...', 'op1.py', '...', '...', 'completed', None, None, None, None, 2.0, 4.0, 1, 2, 0]]
