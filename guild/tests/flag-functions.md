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

    >>> pf("myfun(1e-1, 1.1e-1, [1e-2, 1.1e-2])")
    ('myfun', (0.1, 0.11, [0.01, 0.011]))

## Using flag functions in runs

See [Batch runs - implied random optimizer](batch-implied-random.md).
