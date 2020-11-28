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

When an option includes multiple arguments, the arguments are stored
as a list of flag values.

    >>> pprint(a2f(["--foo", "123", "456", "--bar", "hello", "there"]))
    ({'bar': ['hello', 'there'], 'foo': [123, 456]}, [])

If we include an arg that cannot be converted to a flag:

    >>> pprint(a2f(["other1", "--foo", "123", "--bar", "hello", "there"]))
    ({'bar': ['hello', 'there'], 'foo': 123}, ['other1'])

Options without values are treated as True:

    >>> a2f(["--foo"])
    ({'foo': True}, [])

    >>> pprint(a2f(["--foo", "--bar", "-1.123"]))
    ({'bar': -1.123, 'foo': True}, [])

    >>> pprint(a2f(["--foo", "--bar", "no", "--baz"]))
    ({'bar': False, 'baz': True, 'foo': True}, [])

Short form arguments are supported:

    >>> pprint(a2f(["-a", "bar"]))
    ({'a': 'bar'}, [])

    >>> pprint(a2f(["-abar"]))
    ({'a': 'bar'}, [])

    >>> pprint(a2f(["-abar", "baz"]))
    ({'a': ['bar', 'baz']}, [])

    >>> pprint(a2f(["-abar", "-b"]))
    ({'a': 'bar', 'b': True}, [])

If a negative number is specified as an option value, it is treated as
a number and not as a short form option:

    >>> pprint(a2f(["--x", "-1"]))
    ({'x': -1}, [])

    >>> pprint(a2f(["--x", "-1.123"]))
    ({'x': -1.123}, [])

    >>> pprint(a2f(["--w", "--x", "-1.123", "--y", "-zab"]))
    ({'w': True, 'x': -1.123, 'y': True, 'z': 'ab'}, [])

Converting various types:

    >>> pprint(a2f(["--lr", "0.0001"]))
    ({'lr': 0.0001}, [])

    >>> pprint(a2f(["--lr", "1e-06"]))
    ({'lr': 1e-06}, [])

    >>> pprint(a2f(["--lr", "1.e-06"]))
    ({'lr': 1e-06}, [])

    >>> pprint(a2f(["--lr", "1.123e-06"]))
    ({'lr': 1.123e-06}, [])

    >>> pprint(a2f(["--switch"]))
    ({'switch': True}, [])

    >>> pprint(a2f(["--switch", "yes"]))
    ({'switch': True}, [])

    >>> pprint(a2f(["--switch", "no"]))
    ({'switch': False}, [])

    >>> pprint(a2f(["--name", "Bob", "-e", "123", "-f", "--list", "[4,5,6]"]))
    ({'e': 123, 'f': True, 'list': [4, 5, 6], 'name': 'Bob'}, [])

    >>> pprint(a2f(["foo", "123"]))
    ({}, ['foo', '123'])

Handling various "other arg" cases:

    >>> pprint(a2f(["foo"]))
    ({}, ['foo'])

    >>> pprint(a2f(["foo", "bar"]))
    ({}, ['foo', 'bar'])

    >>> pprint(a2f(["foo", "--bar", "123"]))
    ({'bar': 123}, ['foo'])

A special marker `--` can be used to explicitly specify "other
args". All args preceding the last `--` are always treated as other:

    >>> pprint(a2f(["--foo", "123", "--"]))
    ({}, ['--foo', '123'])

    >>> pprint(a2f(["--foo", "123", "--", "--bar", "456"]))
    ({'bar': 456}, ['--foo', '123'])

    >>> pprint(a2f(["--foo", "123", "--", "--bar", "456", "--"]))
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
    {'run': '1234567e1'}

    >>> p_flags(["run=1e2345671"])
    {'run': '1e2345671'}

    >>> p_flags(["lr=1.0e-06"])
    {'lr': 1e-06}

Note that a float can be forced by adding a decimal:

    >>> p_flags(["num=1234567.0e1"])
    {'num': 12345670.0}

    >>> p_flags(["num=1.0e2345671"])
    {'num': inf}

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

Helper function to print assignments:

    >>> def assigns(flags):
    ...     assigns = op_util.flag_assigns(flags)
    ...     parsed = op_util.parse_flag_assigns(assigns)
    ...     if parsed != flags:
    ...         print("ERROR parsing assignments")
    ...         print("Original flags:")
    ...         pprint(flags)
    ...         print("Assigns (encoded flags):")
    ...         pprint(assigns)
    ...         print("Parsed assigns (decoded flags):")
    ...         pprint(parsed)
    ...         return
    ...     if not assigns:
    ...         print("<empty>")
    ...         return
    ...     for s in assigns:
    ...         print(s)

    >>> assigns({})
    <empty>

Booleans:

    >>> assigns({"b1": True, "b2": False})
    b1=yes
    b2=no

Integers:

    >>> assigns({
    ...     "i1": 0,
    ...     "i2": -123,
    ...     "i3": 123,
    ...     "i4": pow(2, 128),
    ... })
    i1=0
    i2=-123
    i3=123
    i4=340282366920938463463374607431768211456

Floats:

    >>> assigns({
    ...     "f1": 1.0,
    ...     "f2": 1e-1,
    ...     "f3": 1.1e3,
    ...     "f4": -1.123e4,
    ...     "f5": 1/6,
    ... })
    f1=1.0
    f2=0.1
    f3=1100.0
    f4=-11230.0
    f5=0.16666666666666666

Empty strings and None:

    >>> assigns({"e": "", "n": None})
    e=''
    n=null

Strings:

    >>> assigns({
    ...     "s1": "a",
    ...     "s2": "a b",
    ...     "s3": "'1'",
    ...     "s4": "-1.123e4",
    ...     "s5": "123456e2",
    ... })
    s1=a
    s2='a b'
    s3='''1'''
    s4='-1.123e4'
    s5='123456e2'

Lists:

    >>> assigns({
    ...     "l1": [],
    ...     "l2": [1, 2, 3],
    ...     "l3": ["a", "b", "c"],
    ...     "l4": [{"i1": 123, "i2": 456}, "c", None, {"d": True, "e": 1.123}],
    ... })
    l1=[]
    l2=[1, 2, 3]
    l3=[a, b, c]
    l4=[{i1: 123, i2: 456}, c, null, {d: yes, e: 1.123}]

Dicts:

    >>> assigns({
    ...     "d1": {},
    ...     "d2": {"i1": 123, "i2": 123},
    ...     "d3": {"s": "hello", "l": [1, 2, "a", 1.123]},
    ...     "d4": {"a": [1,2,3], "b": 123, "c": {1,2,3}},
    ... })
    d1={}
    d2={i1: 123, i2: 123}
    d3={l: [1, 2, a, 1.123], s: hello}
    d4={a: [1, 2, 3], b: 123, c: !!set {1: null, 2: null, 3: null}}

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
    ...     flag_data = {
    ...         name.replace("_", "-"): val for name, val in kw.items()
    ...     }
    ...     flagdef = FlagDef("test", flag_data, None)
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

### Splittable flags

Flags that are split using `arg-split` are a special case. These flags
are conveyed as a string value that is split into a list of parts when
used for an operation. The flag value itself is retained as a string
but its values are coerced using the flag type.

    >>> coerce("1 2 3", type="float", arg_split=" ")
    '1.0 2.0 3.0'

Confirm that `path` types are coerced to an absolute path.

    >>> paths = coerce("foo bar", type="path", arg_split=" ")

    >>> split_paths = paths.split(" ")
    >>> split_paths
    ['.../guild/tests/foo', '.../guild/tests/bar']

    >>> os.path.isabs(split_paths[0]), split_paths
    (True, ...)

    >>> os.path.isabs(split_paths[1]), split_paths
    (True, ...)

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

Run labels are generated using the function `run_label`.

    >>> from guild.op_util import run_label

Missing template:

    >>> run_label("", {})
    ''

    >>> run_label(None, {})
    ''

    >>> run_label(None, {"foo": "FOO"})
    'foo=FOO'

    >>> run_label(None, {"foo": "FOO", "bar": "BAR"})
    'bar=BAR foo=FOO'

If label is an empty string, it is used rather than the default.

    >>> run_label("", {"foo": "FOO", "bar": "BAR"})
    ''

Floats are truncated:

    >>> run_label(None, {"f": 1.123456789})
    'f=1.12345'

Long paths are shortened to use an ellipsis:

    >>> long_path = path(mkdtemp(), "abc/def/ghi/jkl/mno/pqr/stu/vwx/yz")
    >>> ensure_dir(long_path)
    >>> run_label(None, {"p": long_path})  # doctest: -WINDOWS
    'p=.../\u2026/vwx/yz'

Templates:

    >>> run_label("foo", {})
    'foo'

    >>> run_label("foo", {"foo": "FOO"})
    'foo'

    >>> run_label("${foo}", {})
    ''

    >>> run_label("${foo}", {"foo": "FOO"})
    'FOO'

    >>> run_label("foo: ${foo}", {"foo": "FOO"})
    'foo: FOO'

    >>> run_label(
    ...     "${i} ${f} ${b} ${s} ${l}",
    ...     {"i": 1234, "f": 9.87654321, "b": True, "s": "hello",
    ...      "l": [1, 1.123, "hola"]})
    '1234 9.87654 yes hello [1, 1.123, hola]'

    >>> run_label("a-${b}-c", {})
    'a--c'

    >>> run_label("${b}-c", {})
    '-c'

    >>> run_label("a-${b}", {})
    'a-'

    >>> run_label("a-${b|default:b}-c", {})
    'a-b-c'

    >>> run_label("${b|default:b}-c", {})
    'b-c'

    >>> run_label("a-${b|default:b}", {})
    'a-b'

    >>> run_label("a-${b}-c", {"b": "b"})
    'a-b-c'

    >>> run_label("${b}-c", {"b": "b"})
    'b-c'

    >>> run_label("a-${b}", {"b": "b"})
    'a-b'

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

### Run label filters

Run label filters are used to modify label values. They are applied
using the format ``${NAME|FILTER:ARG1,ARG2}``.

#### basename

`basename` returns the base name for a path.

    >>> run_label("${file|basename}", {"file": path("foo", "bar.txt")})
    'bar.txt'

#### default

`default` provides a value in case a flag is not defined or is `None`.

    >>> run_label("${foo|default:123}", {})
    '123'

    >>> run_label("${foo|default:456}", {"foo": None})
    '456'

    >>> run_label("${foo|default:456}", {"foo": '789'})
    '789'

#### Python formatting strings

The `%` symbol applies Python formatting to a value.

    >>> run_label("${f|%.2f} ${i|%05d}", {"f": 1.123456789, "i": 12})
    '1.12 00012'

An invalid formatting string returns the original value with a
warning:

    >>> with LogCapture() as logs:
    ...     run_label("${s|%z}", {"s": "hello"})
    'hello'

    >>> logs.print_all()
    WARNING: error formatting 'hello' with '%z': unsupported
    format character 'z' (0x7a) at index 1

However, an invalid type for the specified formatting string is
silently ignored:

    >>> with LogCapture() as logs:
    ...     run_label("${s|%.2f}", {"s": "hello"})
    'hello'

    >>> logs.get_all()
    []

#### unquote

`unquote` removes leading and trailing single quotes. This is used for
values that might otherwise appear quoted in a label.

First, a quoted value:

    >>> run_label("ver=${ver}", {"ver": "12345"})
    "ver='12345'"

Use `unquote` to remove the quotes:

    >>> run_label("ver=${ver|unquote}", {"ver": "12345"})
    'ver=12345'

Double quotes are not removed:

    >>> run_label("ver=${ver|unquote}", {"ver": '"12345"'})
    'ver="12345"'

Empty strings and single quote chars are not altered:

    >>> run_label("ver=${ver|unquote}", {"ver": ""})
    'ver='

    >>> run_label("ver=${ver|unquote}", {"ver": "'"})
    "ver='"

None values return empty strings:

    >>> run_label("ver=${ver|unquote}", {"ver": None})
    'ver='

## Split batch file from args

    >>> op_util.split_batch_files([
    ...     "foo",
    ...     "@file-1",
    ...     "bar=123",
    ...     "@file-2",
    ... ])
    (['file-1', 'file-2'], ['foo', 'bar=123'])

## Flag vals for opdef

Helper:

    >>> def flag_vals(opdef, user_flag_vals, force=False):
    ...     flag_vals, resource_flagdefs = (
    ...         op_util.flag_vals_for_opdef(opdef, user_flag_vals, force)
    ...     )
    ...     assert not resource_flagdefs, resource_flagdefs
    ...     pprint(flag_vals)

Empty opdef:

    >>> gf = guildfile.for_string("""
    ... op: { main: guild.pass }
    ... """)

    >>> opdef = gf.default_model["op"]

Empty flag vals:

    >>> flag_vals(opdef, {})
    {}

### No such flags

No such flag, no force:

    >>> flag_vals(opdef, {"foo": 123})
    Traceback (most recent call last):
    NoSuchFlagError: foo

No such flag, force:

    >>> flag_vals(opdef, {"foo": 123}, force=True)
    {'foo': 123}

### Required flag vals

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     required-no-default:
    ...       required: yes
    ...     required-with-default:
    ...       required: yes
    ...       default: 123
    ... """)

    >>> opdef = gf.default_model["op"]

Missing required, no force:

    >>> flag_vals(opdef, {})
    Traceback (most recent call last):
    MissingRequiredFlags: [<guild.guildfile.FlagDef 'required-no-default'>]

Missing required, force:

    >>> flag_vals(opdef, {}, force=True)
    {'required-no-default': None, 'required-with-default': 123}

### Coercing flag vals

Opdef with flag of float type:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     float:
    ...       type: float
    ... """)

    >>> opdef = gf.default_model["op"]

Cannot coerce, no force:

    >>> flag_vals(opdef, {"float": "abc"})
    Traceback (most recent call last):
    InvalidFlagValue: ('abc', <guild.guildfile.FlagDef 'float'>,
    "invalid value for type 'float'")

Cannot coerce, force:

    >>> flag_vals(opdef, {"float": "abc"}, force=True)
    {'float': 'abc'}

Can coerce:

    >>> flag_vals(opdef, {"float": "1.123"})
    {'float': 1.123}

### Flag choices

Opdef with valid default choice:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     s: hi
    ...     i: 123
    ...     choice:
    ...       default: a
    ...       choices:
    ...        - a
    ...        - b
    ...        - value: see
    ...          alias: c
    ...        - value: d
    ...          flags:
    ...            s: hola
    ...            i: 456
    ...        - value: eee
    ...          alias: e
    ...          flags:
    ...            s: ya
    ...            i: 789
    ... """)

    >>> opdef = gf.default_model["op"]

Default:

    >>> flag_vals(opdef, {})
    {'choice': 'a', 'i': 123, 's': 'hi'}

Explicit choice:

    >>> flag_vals(opdef, {"choice": "b"})
    {'choice': 'b', 'i': 123, 's': 'hi'}

Choice with alias:

    >>> flag_vals(opdef, {"choice": "c"})
    {'choice': 'see', 'i': 123, 's': 'hi'}

    >>> flag_vals(opdef, {"choice": "see"})
    {'choice': 'see', 'i': 123, 's': 'hi'}

Choice that defines other flag values:

    >>> flag_vals(opdef, {"choice": "d"})
    {'choice': 'd', 'i': 456, 's': 'hola'}

Choice with both alias and other flag values:

    >>> flag_vals(opdef, {"choice": "e"})
    {'choice': 'eee', 'i': 789, 's': 'ya'}

    >>> flag_vals(opdef, {"choice": "eee"})
    {'choice': 'eee', 'i': 123, 's': 'hi'}

Invalid choice, no force:

    >>> flag_vals(opdef, {"choice": "z"})
    Traceback (most recent call last):
    InvalidFlagChoice: ('z', <guild.guildfile.FlagDef 'choice'>)

Invalid choice, withforce:

    >>> flag_vals(opdef, {"choice": "z"}, force=True)
    {'choice': 'z', 'i': 123, 's': 'hi'}

### Defaults

Opdef with valid default:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     float:
    ...       default: 1.123
    ...       type: float
    ... """)

    >>> opdef = gf.default_model["op"]

    >>> flag_vals(opdef, {})
    {'float': 1.123}

Opdef with invalid default:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     float:
    ...       default: abc
    ...       type: float
    ... """)

    >>> opdef = gf.default_model["op"]

    >>> flag_vals(opdef, {})
    Traceback (most recent call last):
    InvalidFlagValue: ('abc', <guild.guildfile.FlagDef 'float'>,
    "invalid value for type 'float'")

However, we can't set an invalid default:

    >>> flag_vals(opdef, {"float": "abc"})
    Traceback (most recent call last):
    InvalidFlagValue: ('abc', <guild.guildfile.FlagDef 'float'>,
    "invalid value for type 'float'")

### Choice flags

A flag choice can define additional flag vals that are applied when
that choice is selected.

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ...   flags:
    ...     choice:
    ...       default: a
    ...       choices:
    ...         - value: a
    ...           flags:
    ...             a1: 1
    ...             a2: 2
    ...         - value: b
    ...           flags:
    ...             b1: foo
    ...             b2: bar
    ...     a1: null
    ...     b2: bam
    ... """)

    >>> opdef = gf.default_model["op"]

Default choice (="a"):

    >>> flag_vals(opdef, {})
    {'a1': 1, 'a2': 2, 'b2': 'bam', 'choice': 'a'}

Choice "a":

    >>> flag_vals(opdef, {"choice": "a"})
    {'a1': 1, 'a2': 2, 'b2': 'bam', 'choice': 'a'}

Choice "b" - "b2" defined by choice overrides default for "b2" flag:

    >>> flag_vals(opdef, {"choice": "b"})
    {'a1': None, 'b1': 'foo', 'b2': 'bar', 'choice': 'b'}

Choice "b" with explicit value for "b2":

    >>> flag_vals(opdef, {"choice": "b", "b2": "foo"})
    {'a1': None, 'b1': 'foo', 'b2': 'foo', 'choice': 'b'}
