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

### Truncating floats

In some cases, Guild truncates float values to save space (e.g. when
generating default labels that include float
values). `format_flag_val` accepts an optional keyword
`truncate_floats` that can be set to `True` to implement this
behavior.

Here's a helper function:

    >>> trunc = lambda val: run_util.format_flag_val(val, truncate_floats=True)

This option is ignored if the value is not a float:

    >>> trunc(123456789)
    '123456789'

    >>> trunc("hello")
    'hello'

It has no effect on floats with decimal parts that are less than four characters.

    >>> run_util.FLOAT_TRUNCATE_LEN
    4

    >>> trunc(0.1)
    '0.1'

    >>> trunc(0.12)
    '0.12'

    >>> trunc(0.123)
    '0.123'

    >>> trunc(0.1234)
    '0.1234'

When the formatted value would otherwise need more than four
characters, Guild does not truncate:

    >>> trunc(0.12345)
    '0.1234'

    >>> trunc(0.12344)
    '0.1234'

Note that Guild rounds the formatted value.

In the case where the truncated value would be rounded to "1.0", Guild
returns "0.9999".

    >>> trunc(0.99995)
    '0.9999'

Leading digits aren't truncated.

    >>> trunc(12345.12345)
    '12345.1234'

Exponent formatting is use as needed for small numbers:

    >>> trunc(0.0000012345)
    '1.2345e-06'

Any leading digits will precent exponent notation and cause loss of
precision on the decimal part.

    >>> trunc(1.0000012345)
    '1.0000'

    >>> trunc(1.00012345)
    '1.0001'
