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

The function `decode_flag_function` in the `flag_util` module is
responsible for parsing functions.

    >>> from guild import flag_util
    >>> decode = flag_util.decode_flag_function

Anonymous functions must be in the format `[ARG1:ARG2[:REST_ARGS]*`.

The following are NOT anonymous functions:

    >>> decode("[]")
    Traceback (most recent call last):
    ValueError: not a function

    >>> decode("[1]")
    Traceback (most recent call last):
    ValueError: not a function

    >>> decode("[1,2,3]")
    Traceback (most recent call last):
    ValueError: not a function

    >>> encoded = flag_util.encode_flag_val({"a": [1,2,3], "b": 123, "c": {1,2,3}})
    >>> encoded
    '{a: [1, 2, 3], b: 123, c: !!set {1: null, 2: null, 3: null}}'

    >>> decode(encoded)
    Traceback (most recent call last):
    ValueError: not a function

    >>> decode("[this has spaces:yes:[1,2,3]]")
    Traceback (most recent call last):
    ValueError: not a function

Values may be quoted to prevent them from being treated as functions:

    >>> decode("'[1:2]'")
    Traceback (most recent call last):
    ValueError: not a function

    >>> decode("'[1:2:3]'")
    Traceback (most recent call last):
    ValueError: not a function

The following are anonymous functions:

    >>> decode("[1:2]")
    (None, (1, 2))

    >>> decode("[1:2:3]")
    (None, (1, 2, 3))

    >>> decode("[1:2:3:4:5]")
    (None, (1, 2, 3, 4, 5))

Named functions:

    >>> decode("uniform[-2.0:2.0]")
    ('uniform', (-2.0, 2.0))

    >>> decode("log-uniform[-2.0:2.0]")
    ('log-uniform', (-2.0, 2.0))

    >>> decode("foo.bar.baz[-2.0:2.0]")
    ('foo.bar.baz', (-2.0, 2.0))

    >>> decode("three_args[1:2:3]")
    ('three_args', (1, 2, 3))

    >>> decode("four_args[1:2:3:4]")
    ('four_args', (1, 2, 3, 4))

    >>> decode("five_args[1:2:3:4:5]")
    ('five_args', (1, 2, 3, 4, 5))

Names may contain only characters, digits, underscores, dashes, or
dots:

    >>> decode("a^z[1:2:3:4:5]")
    Traceback (most recent call last):
    ValueError: not a function

Arguments may be of any type:.

    >>> decode("[hello:1:1.2]")
    (None, ('hello', 1, 1.2))

    >>> decode("myfun[hello:1:1.2]")
    ('myfun', ('hello', 1, 1.2))

    >>> decode("myfun[this has spaces:no:[1, 2, null]]")
    ('myfun', ('this has spaces', False, [1, 2, None]))

    >>> decode("myfun[1e-1:1.1e-1:[1e-2, 1.1e-2]]")
    ('myfun', (0.1, 0.11, [0.01, 0.011]))

Float args:

    >>> decode("f[1.0:2.0]")
    ('f', (1.0, 2.0))

    >>> decode("f[1e3:1e2]")
    ('f', (1000.0, 100.0))

Functions may contain spaces:

    >>> decode("[a : b : c]")
    (None, ('a', 'b', 'c'))


## Using flag functions in runs

See [Batch runs - implied random optimizer](batch-implied-random.md).
