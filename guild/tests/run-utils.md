# Run Utils

The `run_util` module provides various run related utility functions.

    >>> from guild import run_util

## Formatting flag vals

The `format_flag_val` function formats flag values into strings that
can later be converted back to values using `op_util.parse_arg_val`.

Here's a function that formats a Python value and verifies that the
parsed verion equals the original value.

    >>> from guild import op_util

    >>> def fmt(val):
    ...     formatted = run_util.format_flag_val(val)
    ...     parsed = op_util.parse_arg_val(formatted)
    ...     return formatted, parsed, parsed == val

    >>> fmt("")
    ("''", '', True)

    >>> fmt("a")
    ('a', 'a', True)

    >>> fmt(1)
    ('1', 1, True)

    >>> fmt(1.0)
    ('1.0', 1.0, True)

    >>> fmt(1/3)
    ('0.3333333333333333', 0.3333333333333333, True)

    >>> fmt(True)
    ('yes', True, True)

    >>> fmt(False)
    ('no', False, True)

    >>> fmt(None)
    ('null', None, True)

    >>> fmt(["", "a", 1, 1.0, 1/3, True, False, None])
    ("['', a, 1, 1.0, 0.3333333333333333, yes, no, null]",
     ['', 'a', 1, 1.0, 0.3333333333333333, True, False, None],
     True)
