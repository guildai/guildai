# Batch util

The `batch_util` module implements core batch implementation support
and is used by `batch_main` and optimizers.

    >>> from guild import batch_util

## Functions

A function may be specified for a flag value. Functions have two
forms:

- Slice style
- Named

A slice style function uses Python's slice syntax to represent two or
three numerical values. A named function uses Python's function call
syntax to represent a named list of values.

The `batch_util.parse_function` parses a string into a function
spec. A function spec is a two-tuple of name and an args tuple.

    >>> pf = batch_util.parse_function

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
