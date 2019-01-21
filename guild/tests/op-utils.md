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

If a negative number is specified as an option value, it is treated as
a number and not as a short form option:

    >>> a2f(["--x", "-1"])
    {'x': -1}

    >>> a2f(["--x", "-1.123"])
    {'x': -1.123}

    >>> pprint(a2f(["--w", "--x", "-1.123", "--y", "-zab"]))
    {'w': True, 'x': -1.123, 'y': True, 'z': 'ab'}

## Parsing flags

Use `op_util.parse_flags` to parse a list of `NAME=VAL` args.

    >>> def p_flags(args):
    ...   pprint(op_util.parse_flags(args))

    >>> p_flags([])
    {}

    >>> p_flags(["a=1"])
    {'a': 1}

    >>> p_flags(["a=A"])
    {'a': 'A'}

    >>> p_flags(["a=True", "b=true", "c=yes"])
    {'a': True, 'b': True, 'c': True}

    >>> p_flags(["a=False", "b=false", "c=no"])
    {'a': False, 'b': False, 'c': False}

    >>> p_flags(["a="])
    {'a': ''}

    >>> p_flags(["a=[1,2,3]"])
    {'a': [1, 2, 3]}

    >>> p_flags(["a"])
    Traceback (most recent call last):
    ArgValueError: a

    >>> p_flags([
    ...   "a=['A','B']",
    ...   "c=123",
    ...   "d-e=",
    ...   "f={'a':456,'b':'C'}",
    ...   "g=null"])
    {'a': ['A', 'B'],
     'c': 123,
     'd-e': '',
     'f': {'a': 456, 'b': 'C'},
     'g': None}

 If exponent syntax is used, it must contain a decimal to be converted
 to a float:

    >>> p_flags(["lr=1e-06"])
    {'lr': '1e-06'}

    >>> p_flags(["lr=1.0e-06"])
    {'lr': 1e-06}

## Parsing command line args as flags

Use `op_util.args_to_flags` to parse command line args using `--` and
`-` getopt style options as flags.

    >>> def a2f(args):
    ...   pprint(op_util.args_to_flags(args))

    >>> a2f([])
    {}

    >>> a2f(["--lr", "0.0001"])
    {'lr': 0.0001}

    >>> a2f(["--lr", "1e-06"])
    {'lr': '1e-06'}

    >>> a2f(["--lr", "1.e-06"])
    {'lr': 1e-06}

    >>> a2f(["--lr", "1.123e-06"])
    {'lr': 1.123e-06}

    >>> a2f(["--switch"])
    {'switch': True}

    >>> a2f(["--switch", "yes"])
    {'switch': True}

    >>> a2f(["--switch", "no"])
    {'switch': False}

    >>> a2f(["--name", "Bob", "-e", "123", "-f", "--list", "[4,5,6]"])
    {'e': 123, 'f': True, 'list': [4, 5, 6], 'name': 'Bob'}

Non option style args are ignored:

    >>> a2f(["foo", "123"])
    {}
