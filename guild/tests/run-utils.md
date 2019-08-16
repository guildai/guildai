# Run Utils

The `run_util` module provides various run related utility functions.

    >>> from guild import run_util

## Formatting run attributes

    >>> def fmt(val):
    ...     print(run_util.format_attr(val))

    >>> fmt("1")
    1

    >>> fmt("1.1")
    1.1

    >>> fmt(True)
    yes

    >>> fmt("10")
    10

    >>> fmt([1, 2, "a b", 1/6])
    <BLANKLINE>
      1
      2
      a b
      0.16666666666666666

    >>> fmt({
    ...   "a": "A",
    ...   "b": 1.1,
    ...   "c": 1e100,
    ... })
    <BLANKLINE>
      a: A
      b: 1.1
      c: 1.0e+100
