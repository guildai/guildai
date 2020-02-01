# Flag Utils

The `flag_util` module provides flag val encoding, decoding, and
formatting support.

    >>> from guild import flag_util

## Encoding and decoding flag values

`flag_util` profiles functions for encoding and decoding flag values.

    >>> encode = flag_util.encode_flag_val
    >>> decode = flag_util.decode_flag_val

Given a Python value, `encode` will generate a string value that can
be used in a call to `decode` to produce the original value.

Here's a function that performs this test. It returns a tuple of the
encoded value, the subsequently decoded value and whether or not the
decoded value is equivalent to the original.

    >>> def encode_decode(val):
    ...     encoded = encode(val)
    ...     decoded = decode(encoded)
    ...     return encoded, decoded, decoded == val

Strings:

    >>> encode_decode("")
    ("''", '', True)

    >>> encode_decode("a")
    ('a', 'a', True)

    >>> encode_decode("a b")
    ('a b', 'a b', True)

    >>> encode_decode("'a b'")
    ("'''a b'''", "'a b'", True)

    >>> encode_decode("2018_06_26")
    ("'2018_06_26'", '2018_06_26', True)

Numbers:

    >>> encode_decode(1)
    ('1', 1, True)

    >>> encode_decode(1.0)
    ('1.0', 1.0, True)

    >>> encode_decode(12e3)
    ('12000.0', 12000.0, True)

    >>> encode_decode(1.234e2)
    ('123.4', 123.4, True)

    >>> encode_decode(1.234e-2)
    ('0.01234', 0.01234, True)

    >>> encode_decode(1e100)
    ('1.0e+100', 1e+100, True)

    >>> encode_decode(1/3)
    ('0.3333333333333333', 0.3333333333333333, True)

Numbers as strings:

    >>> encode_decode("1")
    ("'1'", '1', True)

    >>> encode_decode("1.1")
    ("'1.1'", '1.1', True)

    >>> encode_decode("1.2e3")
    ("'1.2e3'", '1.2e3', True)

    >>> encode_decode("12e3")
    ("'12e3'", '12e3', True)

    >>> encode_decode("-1.23e-2")
    ("'-1.23e-2'", '-1.23e-2', True)

    >>> encode_decode("'1'")
    ("'''1'''", "'1'", True)

Booleans:

    >>> encode_decode(True)
    ('yes', True, True)

    >>> encode_decode(False)
    ('no', False, True)

None:

    >>> encode_decode(None)
    ('null', None, True)

Lists:

    >>> encode_decode([])
    ('[]', [], True)

    >>> encode_decode(["", "a", 1, 1.0, 1/3, True, False, None])
    ("['', a, 1, 1.0, 0.3333333333333333, yes, no, null]",
     ['', 'a', 1, 1.0, 0.3333333333333333, True, False, None],
     True)

Dicts:

    >>> encode_decode({})
    ('{}', {}, True)

Capture result to pprint the decoded value:

    >>> encoded, decoded, test = encode_decode({
    ...     "a": 1.123,
    ...     "b": "c d",
    ...     "e": True,
    ...     "f": [1, 2, "g h"]})

    >>> encoded
    '{a: 1.123, b: c d, e: yes, f: [1, 2, g h]}'

    >>> pprint(decoded)
    {'a': 1.123, 'b': 'c d', 'e': True, 'f': [1, 2, 'g h']}

    >>> test
    True

### Formatting flags

Flags can be formatted using the `format_flags` function.

Formatted flags are returned as a sorted list of `NAME=VALUE` where
`VALUE` is the formatted flag value for `NAME`.

Here's a function to print the formatted flags:

    >>> def format(flags, truncate_floats=False):
    ...     formatted = flag_util.format_flags(flags, truncate_floats)
    ...     for s in formatted:
    ...         print(s)

    >>> format({
    ...     "s1": "",
    ...     "s2": "a",
    ...     "s3": "a b",
    ...     "s4": "a b 'c d e'",
    ...     "s5": "12e321",
    ...     "i": 101,
    ...     "f1": 1.1,
    ...     "f2": .1,
    ...     "f3": 1.,
    ...     "f4": 1.234e+3,
    ...     "f5": -1.234e-3,
    ...     "f6": 1/6,
    ... }) # doctest: +REPORT_UDIFF
    f1=1.1
    f2=0.1
    f3=1.0
    f4=1234.0
    f5=-0.001234
    f6=0.16666666666666666
    i=101
    s1=''
    s2=a
    s3='a b'
    s4="a b 'c d e'"
    s5='12e321'

### Truncating floats

Long floats can be truncated when formatting by specifying
`truncate_flags=True`.

    >>> format({"f": 1/6}, truncate_floats=True)
    f=0.16666

Truncation is performed only as needed:

    >>> format({
    ...     "f1": 1.1,
    ...     "f2": 1.12,
    ...     "f3": 1.123,
    ...     "f4": 1.1234,
    ...     "f5": 1.12345,
    ...     "f6": 1.123456,
    ... }, truncate_floats=True)
    f1=1.1
    f2=1.12
    f3=1.123
    f4=1.1234
    f5=1.12345
    f6=1.12345

Truncating does not round up:

    >>> format({
    ...     "f1": 1.123454,
    ...     "f2": 1.123455,
    ...     "f3": 0.999999,
    ... }, truncate_floats=True)
    f1=1.12345
    f2=1.12345
    f3=0.99999

Leading digits aren't truncated.

    >>> format({"f": 12345.123456}, truncate_floats=True)
    f=12345.12345

Exponent formatting is use as needed for small numbers:

    >>> format({"f": 0.0000012345}, truncate_floats=True)
    f=1.2345e-06

For values that cannot be converted to exponent notation, data is
lost:

    >>> format({"f": 1.0000012345}, truncate_floats=True)
    f=1.00000

## Exceptions to YAML decoding

### Anonymouse flag functions

Guild supports a special syntax for [flag
functions](flag-functions.md). In one case, this syntax conflicts with
YAML --- the anonymous flag function, which YAML decodes as a list.

    >>> import yaml

    >>> yaml.safe_load("[1:2]")
    [62]

Guild provides an exception to let the value pass through as a string:

    >>> decode("[1:2]")
    '[1:2]'

### Concatenated lists

Guild provides a shorthand for generating lists that follows Pythons
syntax for [list
concatenation](https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range).

    >>> decode("[1] * 2")
    [1, 1]

White space is ignored:

    >>> decode("[1]*2")
    [1, 1]

    >>> decode(" [1] * 2 ")
    [1, 1]

Other examples:

    >>> decode("[] * 2")
    []

    >>> decode("[1] * 0")
    []

    >>> decode("[1] * 1")
    [1]

    >>> decode("[1,2] * 2")
    [1, 2, 1, 2]

### Sequences

Guild provides a number of flag functions that are expanded to
sequences. These include `range`, `linspace`, and `logspace`.

To log convert warnings, we use a log capture:

    >>> logs = LogCapture(strip_ansi_format=True)

#### `range` function

`range` is used to define a sequence of values that fall within a
range.

    >>> decode("range[1:5]")
    [1, 2, 3, 4, 5]

An increment can be provided:

    >>> decode("range[0:5:2]")
    [0, 2, 4]

Reverse order:

    >>> decode("range[5:1:-1]")
    [5, 4, 3, 2, 1]

Non-integer increments:

    >>> decode("range[1:5:0.5]")
    [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

    >>> decode("range[1e-5:1e-4:1e-5]")
    [1e-05, 2e-05, 3e-05, 4e-05, 5e-05, 6e-05, 7e-05, 8e-05, 9e-05, 0.0001]

Additional arguments are ignored.

    >>> with logs:
    ...     decode("range[1:5:1:2:3]")
    [1, 2, 3, 4, 5]

    >>> logs.print_all()
    WARNING: unsupported arguments for range function: (2, 3) - ignoring

Single arg to range:

    >>> decode("range[10]")
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

String args:

    >>> with logs:
    ...     decode("range[foo:bar]")
    'range[foo:bar]'

    >>> logs.print_all()
    WARNING: error decoding 'range[foo:bar]': invalid arg 'foo': expected a number

Not enough args:

    >>> with logs:
    ...     decode("range[]")
    'range[]'

    >>> logs.print_all()
    WARNING: error decoding 'range[]': function requires at least 1 arg(s)


#### `linspace` function

The `linspace` function is used to generate a sequence given a start,
stop and optional count. By default, Guild expands to a count of 10.

    >>> decode("linspace[1:5]")
    [1.0, 2.0, 3.0, 4.0, 5.0]

    >>> decode("linspace[1:10]")
    [1.0, 3.25, 5.5, 7.75, 10.0]

    >>> decode("linspace[1:10:10]")
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    >>> decode("linspace[1e-2:1e-1:10]")
    [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]

Addition arguments are ignored.

    >>> with logs:
    ...     decode("linspace[1:5:5:hello:456]")
    [1.0, 2.0, 3.0, 4.0, 5.0]

    >>> logs.print_all()
    WARNING: unsupported arguments for linspace function: ('hello', 456) - ignoring

Not enough args:

    >>> with logs:
    ...     decode("linspace[]")
    'linspace[]'

    >>> logs.print_all()
    WARNING: error decoding 'linspace[]': function requires at least 2 arg(s)

Invalid args:

    >>> with logs:
    ...     decode("linspace[1:bar]")
    'linspace[1:bar]'

    >>> logs.print_all()
    WARNING: error decoding 'linspace[1:bar]': invalid arg 'bar': expected a number

#### `logspace` function

`logspace` is like `linspace` but spaces values on a log scale.

`start` and `end` args are applied to a base 10 by default.

    >>> decode("logspace[1:5]")
    [10.0, 100.0, 1000.0, 10000.0, 100000.0]

    >>> decode("logspace[-5:0:6]")
    [1e-05, 0.0001, 0.001, 0.01, 0.1, 1.0]

An alternative base can be provided as a 4th argument.

    >>> decode("logspace[0:3:4:2]")
    [1.0, 2.0, 4.0, 8.0]

Additional arguments are ignored.

    >>> with LogCapture(strip_ansi_format=True) as logs:
    ...    decode("logspace[0:3:4:2:456:hello]")
    [1.0, 2.0, 4.0, 8.0]

    >>> logs.print_all()
    WARNING: unsupported arguments for logspace function: (456, 'hello') - ignoring

Not enough args:

    >>> with logs:
    ...     decode("logspace[]")
    'logspace[]'

    >>> logs.print_all()
    WARNING: error decoding 'logspace[]': function requires at least 2 arg(s)

Invalid args:

    >>> with logs:
    ...     decode("logspace[1:bar]")
    'logspace[1:bar]'

    >>> logs.print_all()
    WARNING: error decoding 'logspace[1:bar]': invalid arg 'bar': expected a number

### Integers with underscores

YAML ignores underscores in integers. So '1_2_3' is parsed as the int
123. This is surprising behavior and Guild makes an exception for such
cases.

Here's a helper to print YAML parsed and Guild decoded values:

    >>> def compare(s):
    ...     return yaml.safe_load(s), decode(s)

    >>> compare("1_2_3")
    (123, '1_2_3')

    >>> compare("1.1_2")
    (1.12, '1.1_2')

    >>> compare("1:2")
    (62, '1:2')

### Short run IDs that resemble scientific notation

Guild run IDs may resemble floating point notation. Guild supports an
exception to the YAML parsing in order to support 8 character short
IDs that resemble scientific notation.

Rules:

- Len at least 3 chars and at most 8
- Does not contain `[-+.]`
- Contains only lower case `e`

Examples:

    >>> short_ids = [
    ...     "67217e15",
    ...     "1e234567",
    ...     "1234e567",
    ...     "1e2",
    ...     "12e3",
    ...     "123e4",
    ...     "1234e5",
    ...     "12345e6",
    ...     "123456e7",
    ... ]

YAML parse vs Guild's `decode` - Guild treats each example as a string
rather than a float:

    >>> for val in short_ids:
    ...     print("%.1f %s" % (yaml.safe_load(val), decode(val)))
    67217000000000000000.0 67217e15
    inf 1e234567
    inf 1234e567
    100.0 1e2
    12000.0 12e3
    1230000.0 123e4
    123400000.0 1234e5
    12345000000.0 12345e6
    1234560000000.0 123456e7

Non-examples:

    >>> not_short_ids = [
    ...     "1234567e8",   # contains more than 8 chars
    ...     "+12345e6",    # contains '+'
    ...     "123456E7",    # uses upper case 'E'
    ...     "1.23455e6",   # contains '.'
    ... ]

Guild's `decode` is equivalent to YAML's:

    >>> for val in not_short_ids:
    ...     print("%.1f %.1f" % (decode(val), yaml.safe_load(val)))
    123456700000000.0 123456700000000.0
    12345000000.0 12345000000.0
    1234560000000.0 1234560000000.0
    1234550.0 1234550.0
