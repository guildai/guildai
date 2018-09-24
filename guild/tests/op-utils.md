# Op utils

The `guild.op_util` module provides helper functions for plugins and
user operations.

    >>> from guild import op_util

## Converting plugin args to flags

Use `args_to_flags` to convert a list of command line args to flag
keyvals.

    >>> a2f = op_util.args_to_flags

    >>> a2f([])
    {}

    >>> a2f(["--foo", "123"])
    {'foo': 123}

    >>> pprint(a2f(["--foo", "123", "--bar", "hello"]))
    {'bar': 'hello', 'foo': 123}

Options without values are treated as True:

    >>> a2f(["--foo"])
    {'foo': True}

    >>> pprint(a2f(["--foo", "--bar", "1.123"]))
    {'bar': 1.123, 'foo': True}

Short form arguments are supported:

    >>> a2f(["-a", "bar"])
    {'a': 'bar'}

    >>> a2f(["-abar"])
    {'a': 'bar'}

If multipe option args are specified, only the last is used:

    >>> a2f(["--foo", "abd", "def"])
    {'foo': 'def'}

## Parsing args

Use `op_util.parse_args` to parse a list of `NAME=VAL` args.

    >>> def p(args):
    ...   pprint(op_util.parse_args(args))

    >>> p([])
    {}

    >>> p(["a=1"])
    {'a': 1}

    >>> p(["a=A"])
    {'a': 'A'}

    >>> p(["a=True"])
    {'a': True}

    >>> p(["a="])
    {'a': None}

    >>> p(["a=[1,2,3]"])
    {'a': [1, 2, 3]}

    >>> p(["a"])
    Traceback (most recent call last):
    ArgValueError: a

    >>> p(["a=['A','B']", "c=123", "d-e=", "f={'a':456,'b':'C'}"])
    {'a': ['A', 'B'],
     'c': 123,
     'd-e': None,
     'f': {'a': 456, 'b': 'C'}}
