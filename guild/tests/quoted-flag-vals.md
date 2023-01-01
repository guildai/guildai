# Quotes Flag Vals

These tests illustrate flag decoding and encoding behavior for quoted
values.

Related tests: [flag-vals](flag-vals.md).

Quoted values are treated as strings rather than as their otherwise
unquoted values.

We use the `quoted-flag-vals` project for these tests.

    >>> use_project("quoted-flag-vals")

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

    >>> flags = "f1=1 f2=1.1 f3=[a,b,c] f4=yes"

In this case we provide an unquoted list of values for `s`, which
results in a batch.

Here is a preview of the commands that will be run:

    >>> run(f"guild run globals.py {flags} --print-cmd")
    ??? -um guild.batch_main
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 a --f4 true
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 b --f4 true
    ... -um guild.op_main globals --f1 1 --f2 1.1 --f3 c --f4 true

Run the operation:

    >>> run(f"guild run globals.py {flags} -y")
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

### Values encoded as strings

    >>> flags = "f1=\"'1'\" f2=\"'1.1'\" f3=\"'[a,b,c]'\" f4=\"'yes'\""

Guild encodes each string as YAML, applying the required quotes for
each value.

    >>> run(f"guild run globals.py {flags} --print-cmd")
    ??? -um guild.op_main globals --f1 "'1'" --f2 "'1.1'" --f3 "'[a,b,c]'" --f4 "'yes'"

When we run the operation, each value is a string.

    >>> run(f"guild run globals.py {flags} --yes")
    '1' <str>
    '1.1' <str>
    '[a,b,c]' <str>
    'yes' <str>

Guild does not support setting Python lists as global values. A list
always triggers a batch.

When encoded as YAML, complex types can be passed through as flag
values.

    >>> flags = "f2='{a: 1.123, b: 2.234}' f3='!!set {1,2,3}' f4='{a: [1,2,3], b: 123, c: !!set {1,2,3}}'"

    >>> run(f"guild run globals.py {flags} --print-cmd")
    ??? -um guild.op_main globals
    --f2 '{a: 1.123, b: 2.234}'
    --f3 '!!set {1: null, 2: null, 3: null}'
    --f4 '{a: [1, 2, 3], b: 123, c: !!set {1: null, 2: null, 3: null}}'

    >>> run(f"guild run globals.py {flags} --yes")
    {'a': 1.123, 'b': 2.234} <dict>
    {1, 2, 3} <set>
    {'a': [1, 2, 3], 'b': 123, 'c': {1, 2, 3}} <dict>

## Args Interface

Flags applied to 'args' destinations are encoded as strings that can
be parsed using Python's core type constructors: string, int, float,
and bool.

As with any interface, list values drive batch runs with args. Here's
the same set of flags we used to star the `globals` test above.

    >>> flags = "f1=1 f2=1.1 f3=[a,b,c] f4=yes"

The command preview shows the batch and the three generated runs.

    >>> run(f"guild run args.py {flags} --print-cmd")
    ??? -um guild.batch_main
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 a --f4 1
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 b --f4 1
    ... -um guild.op_main args --f1 1 --f2 1.1 --f3 c --f4 1

Run the operation.

    >>> run(f"guild run args.py {flags} --yes")
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

    >>> flags = "f1=2 f2=2.2 f3=hola f4=no"

    >>> run(f"guild run args.py {flags} --print-cmd")
    ??? -um guild.op_main args --f1 2 --f2 2.2 --f3 hola --f4 ''

    >>> run(f"guild run args.py {flags} --yes")
    2 <int>
    2.2 <float>
    'hola' <str>
    False <bool>

Guild imports type settings for args and can validate input to the
command.

    >>> run("guild run args.py f1=one -y")
    guild: invalid value one for f1: invalid value for type 'int'
    <exit 1>

We can pass any string through to a string arg (flag `f3` in this
case).

    >>> flags="f1=2 f2=2.2 f3=\"'[1,2,3]'\" f4=yes"

    >>> run(f"guild run args.py {flags} --print-cmd")
    ??? -um guild.op_main args --f1 2 --f2 2.2 --f3 '[1,2,3]' --f4 1

    >>> run(f"guild run args.py {flags} --yes")
    2 <int>
    2.2 <float>
    '[1,2,3]' <str>
    True <bool>

When we pass complex types, they are converted to strings using
Python's `str` type contructor.

    >>> flags = "f5='{a: 1.123, b: 2.234}' f6='!!set {1,2,3}' f7='{a: [1,2,3], b: 123, c: !!set {1,2,3}}'"

    >>> run(f"guild run args.py {flags} --force-flags --print-cmd")
    ??? -um guild.op_main args --f1 1 --f2 1.1 --f3 hello --f4 ''
    --f5 '{'"'"'a'"'"': 1.123, '"'"'b'"'"': 2.234}'
    --f6 '{1, 2, 3}'
    --f7 '{'"'"'a'"'"': [1, 2, 3], '"'"'b'"'"': 123, '"'"'c'"'"': {1, 2, 3}}'

    >>> run(f"guild run args.py {flags} --force-flags --yes")  # doctest: +REPORT_UDIFF
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
