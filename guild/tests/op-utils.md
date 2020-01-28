# Op utils

The `guild.op_util` module provides helper functions for plugins and
user operations.

    >>> from guild import op_util

## Converting plugin args to flags

Use `args_to_flags` to convert a list of command line args to flag
keyvals. Result includes a list of "other args" that cannot be
converted to flags.

    >>> a2f = op_util.args_to_flags

    >>> a2f([])
    ({}, [])

    >>> a2f(["--foo", "123"])
    ({'foo': 123}, [])

    >>> pprint(a2f(["--foo", "123", "--bar", "hello"]))
    ({'bar': 'hello', 'foo': 123}, [])

If we include an arg that cannot be converted to a flag:

    >>> pprint(a2f(["other1", "--foo", "123", "--bar", "hello", "other2"]))
    ({'bar': 'hello', 'foo': 123}, ['other1', 'other2'])

Options without values are treated as True:

    >>> a2f(["--foo"])
    ({'foo': True}, [])

    >>> pprint(a2f(["--foo", "--bar", "1.123"]))
    ({'bar': 1.123, 'foo': True}, [])

Short form arguments are supported:

    >>> a2f(["-a", "bar"])
    ({'a': 'bar'}, [])

    >>> a2f(["-abar"])
    ({'a': 'bar'}, [])

If a negative number is specified as an option value, it is treated as
a number and not as a short form option:

    >>> a2f(["--x", "-1"])
    ({'x': -1}, [])

    >>> a2f(["--x", "-1.123"])
    ({'x': -1.123}, [])

    >>> pprint(a2f(["--w", "--x", "-1.123", "--y", "-zab"]))
    ({'w': True, 'x': -1.123, 'y': True, 'z': 'ab'}, [])

Converting various types:

    >>> a2f(["--lr", "0.0001"])
    ({'lr': 0.0001}, [])

    >>> a2f(["--lr", "1e-06"])
    ({'lr': 1e-06}, [])

    >>> a2f(["--lr", "1.e-06"])
    ({'lr': 1e-06}, [])

    >>> a2f(["--lr", "1.123e-06"])
    ({'lr': 1.123e-06}, [])

    >>> a2f(["--switch"])
    ({'switch': True}, [])

    >>> a2f(["--switch", "yes"])
    ({'switch': True}, [])

    >>> a2f(["--switch", "no"])
    ({'switch': False}, [])

    >>> pprint(a2f(["--name", "Bob", "-e", "123", "-f", "--list", "[4,5,6]"]))
    ({'e': 123, 'f': True, 'list': [4, 5, 6], 'name': 'Bob'}, [])

    >>> a2f(["foo", "123"])
    ({}, ['foo', '123'])

Handling various "other arg" cases:

    >>> a2f(["foo"])
    ({}, ['foo'])

    >>> a2f(["foo", "bar"])
    ({}, ['foo', 'bar'])

    >>> a2f(["--foo", "123", "456"])
    ({'foo': 123}, ['456'])

    >>> a2f(["foo", "--bar", "123"])
    ({'bar': 123}, ['foo'])

A special marker `--` can be used to explicitly specify "other
args". All args preceding the last `--` are always treated as other:

    >>> a2f(["--foo", "123", "--"])
    ({}, ['--foo', '123'])

    >>> a2f(["--foo", "123", "--", "--bar", "456"])
    ({'bar': 456}, ['--foo', '123'])

    >>> a2f(["--foo", "123", "--", "--bar", "456", "--"])
    ({}, ['--foo', '123', '--', '--bar', '456'])

## Parsing flags

Use `op_util.parse_flags` to parse a list of `NAME=VAL` args.

    >>> def p_flags(args):
    ...   pprint(op_util.parse_flag_assigns(args))

Empty arg list:

    >>> p_flags([])
    {}

Integers:

    >>> p_flags(["a=1"])
    {'a': 1}

Floats:

    >>> p_flags(["a=1.1", "b=.1", "c=1.", "d=1.e1", "e=1.2e2"])
    {'a': 1.1, 'b': 0.1, 'c': 1.0, 'd': 10.0, 'e': 120.0}

Float exceptions (special handling for run ID strings):

    >>> p_flags(["a=1e1", "b=12e2", "c=123e3", "d=123456e7"])
    {'a': '1e1', 'b': '12e2', 'c': '123e3', 'd': '123456e7'}

Various exponent notation:

    >>> p_flags(["lr=1e-06"])
    {'lr': 1e-06}

    >>> p_flags(["run=1234567e1"])
    {'run': 12345670.0}

    >>> p_flags(["run=1e2345671"])
    {'run': inf}

    >>> p_flags(["lr=1.0e-06"])
    {'lr': 1e-06}

Strings:

    >>> p_flags(["a=A"])
    {'a': 'A'}

Quoted numbers:

    >>> p_flags(["a='1'", "b=\"2\"", "c='1e3'"])
    {'a': '1', 'b': '2', 'c': '1e3'}

    >>> p_flags(["run='1234567e1'"])
    {'run': '1234567e1'}

    >>> p_flags(["run='1e2345671'"])
    {'run': '1e2345671'}

Booleans:

    >>> p_flags(["a=True", "b=true", "c=yes"])
    {'a': True, 'b': True, 'c': True}

    >>> p_flags(["a=False", "b=false", "c=no"])
    {'a': False, 'b': False, 'c': False}

Empty values:

    >>> p_flags(["a="])
    {'a': ''}

Lists:

    >>> p_flags(["a=[1,2,3,a,b,1.,1.2]"])
    {'a': [1, 2, 3, 'a', 'b', 1.0, 1.2]}

Missing '=':

    >>> p_flags(["a"])
    Traceback (most recent call last):
    ArgValueError: a

Various values:

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

## Encoding flag assignments

The function `op_util.flag_assigns` is used to generate a list of flag
assignments. These can be used as flag arguments.

Here's a helper function to print assignments:

    >>> def assigns(flags):
    ...     assigns = op_util.flag_assigns(flags)
    ...     if not assigns:
    ...         print("<empty>")
    ...         return
    ...     for s in assigns:
    ...         print(s)

    >>> assigns({})
    <empty>

    >>> assigns({
    ...     "b1": True,
    ...     "b2": False,
    ...     "d": {"a": 1.123, "b": "c d", "e": True},
    ...     "e": "",
    ...     "f1": 1.1,
    ...     "f2": 1.,
    ...     "f3": .1,
    ...     "f4": 1/6,
    ...     "f5": 0.000012345,
    ...     "i": 312,
    ...     "l": [1, 2, "a", "b c 'd e'"],
    ...     "n": None,
    ...     "s1": "a",
    ...     "s2": "a b",
    ...     "s3": "'1'",
    ...     "s4": "-1.123e4",
    ...     "s5": "123456e2",
    ... }) # doctest: +REPORT_UDIFF
    b1=yes
    b2=no
    d={a: 1.123, b: c d, e: yes}
    e=''
    f1=1.1
    f2=1.0
    f3=0.1
    f4=0.16666666666666666
    f5=1.2345e-05
    i=312
    l=[1, 2, a, b c 'd e']
    n=null
    s1=a
    s2='a b'
    s3='''1'''
    s4='-1.123e4'
    s5='123456e2'

## Global dest

The function `global_dest` applies a dict of flags to a global
destination, returning a globals dict. Global destination is a string
of names separated by dots, each dot generating a named sub-dict
within its parent.

    >>> def global_dest(name, flags):
    ...     pprint(op_util.global_dest(name, flags))

Top-level dest named "foo" with no flags:

    >>> global_dest("foo", {})
    {'foo': {}}

Same top-level with flags:

    >>> global_dest("foo", {"a": 1, "b": 2})
    {'foo': {'a': 1, 'b': 2}}

Multi-level dest:

    >>> global_dest("foo.bar", {"a": 1, "b": 2})
    {'foo': {'bar': {'a': 1, 'b': 2}}}

    >>> global_dest("foo.bar.baz", {"a": 1, "b": 2})
    {'foo': {'bar': {'baz': {'a': 1, 'b': 2}}}}

## Coerce flag vals

The function `coerce_flag_value` is used to coerce flag values into
legal values based on a flag definition.

To illustrate, we'll use a helper function:

    >>> def coerce(val, **kw):
    ...     from guild.guildfile import FlagDef
    ...     flagdef = FlagDef("test", kw, None)
    ...     return op_util.coerce_flag_value(val, flagdef)

Floats:

    >>> coerce(1, type="float")
    1.0

    >>> coerce("1", type="float")
    1.0

    >>> coerce("1.1", type="float")
    1.1

    >>> coerce("nan", type="float")
    nan

    >>> coerce("invalid", type="float")
    Traceback (most recent call last):
    ValueError: invalid value for type 'float'

Ints:

    >>> coerce(1, type="int")
    1

    >>> coerce(1.0, type="int")
    Traceback (most recent call last):
    ValueError: invalid value for type 'int'

    >>> coerce("1", type="int")
    1

    >>> coerce("invalid", type="int")
    Traceback (most recent call last):
    ValueError: invalid value for type 'int'

Numbers (int or float):

    >>> coerce(1, type="number")
    1

    >>> coerce(1.0, type="number")
    1.0

    >>> coerce("invalid", type="number")
    Traceback (most recent call last):
    ValueError: invalid value for type 'number'

Booleans:

    >>> coerce(0, type="boolean")
    False

    >>> coerce(1, type="boolean")
    True

    >>> coerce("", type="boolean")
    False

    >>> coerce("hi", type="boolean")
    True

    >>> coerce("false", type="boolean")
    True

Lists of values:

    >>> coerce([1, 1.0], type="number")
    [1, 1.0]

    >>> coerce([1, 1.0, "invalid"], type="number")
    Traceback (most recent call last):
    ValueError: invalid value for type 'number'

## Validating flag vals

We can validate a list of flag values against an operation def using
`validate_flag_vals`.

Here's an operation to test with:

    >>> from guild import guildfile
    >>> gf = guildfile.for_string("""
    ... test:
    ...   flags:
    ...     choice:
    ...       choices: [1,2,3]
    ...     required:
    ...       required: yes
    ...     range:
    ...       min: 0.0
    ...       max: 1.0
    ... """)
    >>> opdef = gf.default_model.operations[0]

And a helper function to validate:

    >>> def validate(skip_required=False, **vals):
    ...     if not skip_required:
    ...         vals["required"] = "some val"
    ...     op_util.validate_flag_vals(vals, opdef)

Choices:

    >>> validate(choice=1)

    >>> validate(choice=4)
    Traceback (most recent call last):
    InvalidFlagChoice: (4, <guild.guildfile.FlagDef 'choice'>)

Missing required val:

    >>> validate(skip_required=True)
    Traceback (most recent call last):
    MissingRequiredFlags: [<guild.guildfile.FlagDef 'required'>]

Range:

    >>> validate(range=0.0)

    >>> validate(range=1.0)

    >>> validate(range=-1)
    Traceback (most recent call last):
    InvalidFlagValue: (-1, <guild.guildfile.FlagDef 'range'>,
    'out of range (less than min 0.0)')

    >>> validate(range=1.1)
    Traceback (most recent call last):
    InvalidFlagValue: (1.1, <guild.guildfile.FlagDef 'range'>,
    'out of range (greater than max 1.0)')

## Parsing op specs

`op_util.parse_opspec` is used to parse op specs into model_ref,
op_name tuples.

    >>> from guild.op_util import parse_opspec

Helper to raise exception if parse fails:

    >>> def parse(spec):
    ...     parsed = parse_opspec(spec)
    ...     if not parsed:
    ...         raise ValueError(spec)
    ...     return parsed

Empty cases:

    >>> parse(None)
    (None, None)

    >>> parse("")
    (None, None)

Just the operation name:

    >>> parse("op")
    (None, 'op')

Explicit empty model with operation:

    >>> parse(":op")
    ('', 'op')

Model and op:

    >>> parse("model:op")
    ('model', 'op')

Package and op:

    >>> parse("package/op")
    ('package/', 'op')

    >>> parse("package/:op")
    ('package/', 'op')

Pakcage, model, and op:

    >>> parse("package/model:op")
    ('package/model', 'op')

Invalid:

    >>> parse("a:b:c")
    Traceback (most recent call last):
    ValueError: a:b:c

    >>> parse("a/b/c")
    Traceback (most recent call last):
    ValueError: a/b/c

    >>> parse("a:b/c")
    Traceback (most recent call last):
    ValueError: a:b/c

    >>> parse("a/b:c:d")
    Traceback (most recent call last):
    ValueError: a/b:c:d

    >>> parse("a/b:c/d")
    Traceback (most recent call last):
    ValueError: a/b:c/d

    >>> parse("a:b/c:d")
    Traceback (most recent call last):
    ValueError: a:b/c:d

## Run labels

    >>> from guild.op_util import run_label

Missing template:

    >>> run_label("", {})
    ''

    >>> run_label(None, {})
    ''

    >>> run_label(None, {"foo": "FOO"})
    'foo=FOO'

    >>> run_label("", {"foo": "FOO", "bar": "BAR"})
    'bar=BAR foo=FOO'

Templates:

    >>> run_label("foo", {})
    'foo'

    >>> run_label("foo", {"foo": "FOO"})
    'foo'

Flag references:

    >>> run_label("${foo}", {})
    ''

    >>> run_label("${foo}", {"foo": "FOO"})
    'FOO'

    >>> run_label("foo: ${foo}", {"foo": "FOO"})
    'foo: FOO'

Use of default label:

    >>> run_label("${default_label}", {})
    ''

    >>> run_label("${default_label}", {"foo": "FOO", "bar": "BAR"})
    'bar=BAR foo=FOO'

    >>> run_label("prefix ${default_label}", {"foo": "FOO", "bar": "BAR"})
    'prefix bar=BAR foo=FOO'

    >>> run_label("${default_label} suffix", {"foo": "FOO", "bar": "BAR"})
    'bar=BAR foo=FOO suffix'

    >>> run_label("prefix ${default_label} suffix", {"foo": "FOO", "bar": "BAR"})
    'prefix bar=BAR foo=FOO suffix'

Value formatting:

    >>> run_label(None, {"f1": 1.0, "f2": 1.0/3.0, "b1": True, "b2": False, "i": 123})
    'b1=yes b2=no f1=1.0 f2=0.33333 i=123'
