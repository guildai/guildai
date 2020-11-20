# Quotes Flag Vals

These tests illustrate flag decoding and encoding behavior for quoted
values.

Related tests: [flag-vals](flag-vals.md).

Quoted values are treated as strings rather than as their otherwise
unquoted values.

We use the `quoted-flag-vals` project for these tests.

    >>> project = Project(sample("projects", "quoted-flag-vals"))

## Globals Interface

Flags applied to 'globals' or 'global:<name>' destinations are encoded
using YAML. This allows `guild.op_main` to decode to the correct type
without additional type information (e.g. as is the case with
`argparse` parsers).

The script `globals.py` uses None values for its globals to ensure
that type information isn't used to convert values provided in the
tests below. Default flag values impart an implicit flag type. Setting
values to None defines the flags without types.

Here are some flag values that we initially assign:

    >>> flag_vals = {
    ...     "f1": 1,
    ...     "f2": 1.1,
    ...     "f3": ["a", "b", "c"],
    ...     "f4": True
    ... }

In this case we provide an unquoted list of values for `s`, which
results in a batch.

Here is a preview of the commands that will be run:

    >>> project.run("globals.py", flag_vals, print_cmd=True)
    ??? -um guild.batch_main
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 a --f4 true
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 b --f4 true
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 c --f4 true

Run the operation:

    >>> project.run("globals.py", flag_vals)
    INFO: [guild] Running trial ...: globals.py (f1=1, f2=1.1, f3=a, f4=yes)
    1 <int>
    1.1 <float>
    'a' <str>
    True <bool>
    INFO: [guild] Running trial ...: globals.py (f1=1, f2=1.1, f3=b, f4=yes)
    1 <int>
    1.1 <float>
    'b' <str>
    True <bool>
    INFO: [guild] Running trial ...: globals.py (f1=1, f2=1.1, f3=c, f4=yes)
    1 <int>
    1.1 <float>
    'c' <str>
    True <bool>

Here are some examples

In this scenario, we provide the same values as strings.

    >>> flag_vals = {
    ...     "f1": "1",
    ...     "f2": "1.1",
    ...     "f3": '["a", "b", "c"]',
    ...     "f4": "yes"
    ... }

Guild encodes each string as YAML, applying the required quotes for
each value.

    >>> project.run("globals.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main globals --f1 "'1'" --f2 "'1.1'" --f3 "'["a", "b", "c"]'" --f4 "'yes'"

When we run the operation, each value is a string.

    >>> project.run("globals.py", flag_vals)
    '1' <str>
    '1.1' <str>
    '["a", "b", "c"]' <str>
    'yes' <str>

Here are some alternative quoted lists.

    >>> project.run("globals.py", {"f3": "['a','b','c']"})
    "['a','b','c']" <str>

    >>> project.run("globals.py", {"f3": "[a,b,c]"})
    '[a,b,c]' <str>

Note that Guild does not support setting Python lists as global
values. A list always triggers a batch.

Tuples generate a batch as if they were a list (YAML doesn't support
encoding tuples and so tuples are implicitly treated as lists).

    >>> project.run("globals.py", {"f1": (2, 3)})
    INFO: [guild] Running trial ...: globals.py (f1=2)
    2 <int>
    INFO: [guild] Running trial ...: globals.py (f1=3)
    3 <int>

Complex types can be passed through.

    >>> flag_vals = {
    ...     "f2": {"a": 1.123, "b": 2.234},
    ...     "f3": {1,2,3},
    ...     "f4": {"a": [1,2,3], "b": 123, "c": {1,2,3}}
    ... }

    >>> project.run("globals.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main globals
          --f2 '{a: 1.123, b: 2.234}'
          --f3 '!!set {1: null, 2: null, 3: null}'
          --f4 '{a: [1, 2, 3], b: 123, c: !!set {1: null, 2: null, 3: null}}'

    >>> project.run("globals.py", flag_vals) # doctest: -PY3
    {'a': 1.123, 'b': 2.234} <dict>
    set([1, 2, 3]) <set>
    {'a': [1, 2, 3], 'b': 123, 'c': set([1, 2, 3])} <dict>

    >>> project.run("globals.py", flag_vals) # doctest: -PY2
    {'a': 1.123, 'b': 2.234} <dict>
    {1, 2, 3} <set>
    {'a': [1, 2, 3], 'b': 123, 'c': {1, 2, 3}} <dict>

To pass through as string, they must be quoted.

    >>> flag_vals = {
    ...     "f2": '{"a": 1.123, "b": 2.234}',
    ...     "f3": '{1,2,3}',
    ...     "f4": '{"a": [1,2,3], "b": 123, "c": {1,2,3}}}'
    ... }

    >> project.run("globals.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main globals
            --f2 "'{"a": 1.123, "b": 2.234}'"
            --f3 "'{1,2,3}'"
            --f4 "'{"a": [1,2,3], "b": 123, "c": {1,2,3}}}'"

    >>> project.run("globals.py", flag_vals)
    '{"a": 1.123, "b": 2.234}' <str>
    '{1,2,3}' <str>
    '{"a": [1,2,3], "b": 123, "c": {1,2,3}}}' <str>

## Args Interface

Flags applied to 'args' destinations are encoded as strings that can
be parsed using Python's core type constructors: string, int, float,
and bool.

As with any interface, list values drive batch runs with args. Here's
the same set of flags we used to star the `globals` test above.

    >>> flag_vals = {
    ...     "f1": 1,
    ...     "f2": 1.1,
    ...     "f3": ["a", "b", "c"],
    ...     "f4": True
    ... }

The command preview for these flags with the `args.py` script:

    >>> project.run("args.py", flag_vals, print_cmd=True)
    ??? -um guild.batch_main
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 a --f4 1
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 b --f4 1
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 c --f4 1

Run the operation:

    >>> project.run("args.py", flag_vals)
    INFO: [guild] Running trial ...: args.py (f1=1, f2=1.1, f3=a, f4=yes)
    1 <int>
    1.1 <float>
    'a' <str>
    True <bool>
    INFO: [guild] Running trial ...: args.py (f1=1, f2=1.1, f3=b, f4=yes)
    1 <int>
    1.1 <float>
    'b' <str>
    True <bool>
    INFO: [guild] Running trial ...: args.py (f1=1, f2=1.1, f3=c, f4=yes)
    1 <int>
    1.1 <float>
    'c' <str>
    True <bool>

Some some alternative values:

    >>> flag_vals = {
    ...     "f1": 2,
    ...     "f2": 2.2,
    ...     "f3": "hola",
    ...     "f4": False
    ... }

    >>> project.run("args.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main args --f1 2 --f2 2.2 --f3 hola --f4 ''

    >>> project.run("args.py", flag_vals)
    2 <int>
    2.2 <float>
    'hola' <str>
    False <bool>

Because arg parsing scripts apply type conversions, if we pass values
with invalid types, the script fails with an error.

    >>> flag_vals = {"f1": "one"}

    >>> project.run("args.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main args --f1 one --f2 1.1 --f3 hello --f4 ''

    >>> project.run("args.py", flag_vals)
    usage: args.py [-h] [--f1 F1] [--f2 F2] [--f3 F3] [--f4 F4]
    args.py: error: argument --f1: invalid int value: 'one'
    <exit 2>

We can pass any string through to a string arg (flag `f3` in this
case).

    >>> flag_vals = {
    ...     "f1": 2,
    ...     "f2": 2.2,
    ...     "f3": "[1,2,3]",
    ...     "f4": True
    ... }

    >>> project.run("args.py", flag_vals, print_cmd=True)
    ??? -um guild.op_main args --f1 2 --f2 2.2 --f3 '[1,2,3]' --f4 1

    >>> project.run("args.py", flag_vals)
    2 <int>
    2.2 <float>
    '[1,2,3]' <str>
    True <bool>

When we try to pass complex types as arg, they are converts to strings
using Python's `str` type contructor.

    >>> flag_vals = {
    ...     "f5": {"a": 1.123, "b": 2.234},
    ...     "f6": {1,2,3},
    ...     "f7": {"a": [1,2,3], "b": 123, "c": {1,2,3}}
    ... }

We can use `force_args` to pass through unsupported options to
`args.py`.

    >>> project.run("args.py", flag_vals, force_flags=True, print_cmd=True) # doctest: -PY3
    ??? -um guild.op_main args
            --f1 1
            --f2 1.1
            --f3 hello
            --f4 ''
            --f5 '{'"'"'a'"'"': 1.123, '"'"'b'"'"': 2.234}'
            --f6 'set([1, 2, 3])'
            --f7 '{'"'"'a'"'"': [1, 2, 3], '"'"'b'"'"': 123, '"'"'c'"'"': set([1, 2, 3])}'

    >>> project.run("args.py", flag_vals, force_flags=True, print_cmd=True) # doctest: -PY2
    ??? -um guild.op_main args
            --f1 1
            --f2 1.1
            --f3 hello
            --f4 ''
            --f5 '{'"'"'a'"'"': 1.123, '"'"'b'"'"': 2.234}'
            --f6 '{1, 2, 3}'
            --f7 '{'"'"'a'"'"': [1, 2, 3], '"'"'b'"'"': 123, '"'"'c'"'"': {1, 2, 3}}'

The values printed from the script:

    >>> project.run("args.py", flag_vals, force_flags=True) # doctest: -PY3
    1 <int>
    1.1 <float>
    'hello' <str>
    False <bool>
    '--f5' <str>
    "{'a': 1.123, 'b': 2.234}" <str>
    '--f6' <str>
    'set([1, 2, 3])' <str>
    '--f7' <str>
    "{'a': [1, 2, 3], 'b': 123, 'c': set([1, 2, 3])}" <str>

    >>> project.run("args.py", flag_vals, force_flags=True) # doctest: -PY2
    1 <int>
    1.1 <float>
    'hello' <str>
    False <bool>
    '--f5' <str>
    "{'a': 1.123, 'b': 2.234}" <str>
    '--f6' <str>
    '{1, 2, 3}' <str>
    '--f7' <str>
    "{'a': [1, 2, 3], 'b': 123, 'c': {1, 2, 3}}" <str>
