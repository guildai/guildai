# Flag functions

Flag functions are specifying using one of two forms:

    '[' N ( ':' M )* ']'

    NAME '(' N ( ',' M )* ')'

The first form is a slice format, or an unnamed function, while the
second form is a named function.

Example of a slice format:

    [1e-4:1e-1]

Example of a named function:

    uniform(1e-4,1e-1)

## Parsing flag functions

The function `parse_function` in the `op_util` module is responsible
for parsing functions.

    >>> from guild import op_util
    >>> pf = op_util.parse_function

The slice syntax:

    >>> pf("[1:2]")
    (None, (1, 2))

    >>> pf("[1:2:3]")
    (None, (1, 2, 3))

    >>> pf("[1:2:3:4:5]")
    (None, (1, 2, 3, 4, 5))

If a slice-like expression does not contain at least two elements, it
is not considered a function:

    >>> pf("[]")
    Traceback (most recent call last):
    ValueError: not a function

    >>> pf("[1]")
    Traceback (most recent call last):
    ValueError: not a function

The named syntax:

    >>> pf("uniform(-2.0,2.0)")
    ('uniform', (-2.0, 2.0))

Arguments may be of any type, in both slice and named forms.

    >>> pf("[hello:1:1.2]")
    (None, ('hello', 1, 1.2))

    >>> pf("[this has spaces:yes:[1,2,3]]")
    (None, ('this has spaces', True, [1, 2, 3]))

    >>> pf("myfun(hello, 1, 1.2)")
    ('myfun', ('hello', 1, 1.2))

    >>> pf("myfun(this has spaces, no, [1, 2, null])")
    ('myfun', ('this has spaces', False, [1, 2, None]))

## Using flag functions in runs

When a flag function is specified for an optimized batch - i.e. a
batch with an explicit optimizer - it is passed through to the
optimizer unmodified.

However, when specified for a non-optimized batch - i.e. a run with a
flag list value - or for a normal run, Guild resolves the flag value
by applying the function.

For our tests, we'll use the `optimizers` sample project.

    >>> project = Project(sample("projects", "optimizers"))

We'll start by running `echo` with a non-function string value for
`x`, which will cause an error because `x` is defined by `echo as a
float.

    >>> project.run("echo", flags={"x": "badvalue"})
    guild: cannot apply 'badvalue' to flag 'x': invalid value for type 'float'
    <exit 1>

Let's now use a string value that's a valid flag function:

    >>> project.run("echo", flags={"x": "[0:1]"})
    0... 2 'a'

In this case, Guild converted the slice formatted function to a random
value.

We can limit the range to get a predictable value:

    >>> project.run("echo", flags={"x": "[1:1]"})
    1.0 2 'a'

The slice format is equivalent to using the 'uniform' function:

    >>> project.run("echo", flags={"x": "uniform(1,1)"})
    1.0 2 'a'

If an unsupported function is specified, Guild exits with an error:

    >>> project.run("echo", flags={"x": "normal(1,1)"})
    guild: unsupported function 'normal'
    <exit 1>
