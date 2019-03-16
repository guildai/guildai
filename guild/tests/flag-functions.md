# Flag functions

Flag functions are specifying using the format:

    NAME? '[' N? ( ':' M )* ']'

The format resembles Python's slice format. It may have an optional
name preceding the opening bracket.

Example of an unnamed function:

    [1e-4:1e-1]

Example of a named function:

    uniform[1e-4:1e-1]

## Parsing flag functions

The function `parse_function` in the `op_util` module is responsible
for parsing functions.

    >>> from guild import op_util
    >>> pf = op_util.parse_function

Unnamed functions:

    >>> pf("[]")
    (None, ())

    >>> pf("[1]")
    (None, (1,))

    >>> pf("[1:2]")
    (None, (1, 2))

    >>> pf("[1:2:3]")
    (None, (1, 2, 3))

    >>> pf("[1:2:3:4:5]")
    (None, (1, 2, 3, 4, 5))

Named functions:

    >>> pf("uniform[-2.0:2.0]")
    ('uniform', (-2.0, 2.0))

    >>> pf("log-uniform[-2.0:2.0]")
    ('log-uniform', (-2.0, 2.0))

    >>> pf("foo.bar.baz[-2.0:2.0]")
    ('foo.bar.baz', (-2.0, 2.0))

    >>> pf("three_args[1:2:3]")
    ('three_args', (1, 2, 3))

    >>> pf("four_args[1:2:3:4]")
    ('four_args', (1, 2, 3, 4))

    >>> pf("five_args[1:2:3:4:5]")
    ('five_args', (1, 2, 3, 4, 5))

Names may contain only characters, digits, underscores, dashes, or
dots:

    >>> pf("a^z[1:2:3:4:5]")
    Traceback (most recent call last):
    ValueError: not a function

Arguments may be of any type:.

    >>> pf("[hello:1:1.2]")
    (None, ('hello', 1, 1.2))

    >>> pf("[this has spaces:yes:[1,2,3]]")
    (None, ('this has spaces', True, [1, 2, 3]))

    >>> pf("myfun[hello:1:1.2]")
    ('myfun', ('hello', 1, 1.2))

    >>> pf("myfun[this has spaces:no:[1, 2, null]]")
    ('myfun', ('this has spaces', False, [1, 2, None]))

    >>> pf("myfun[1e-1:1.1e-1:[1e-2, 1.1e-2]]")
    ('myfun', (0.1, 0.11, [0.01, 0.011]))

Functions may contain spaces:

    >>> pf("[a : b : c]")
    (None, ('a', 'b', 'c'))

## Using flag functions in runs

See [Batch runs - implied random optimizer](batch-implied-random.md).
