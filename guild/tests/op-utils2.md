# Op Utils

    >>> from guild import op_util2 as op_util

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
    ...     flag_vals = op_util.flag_vals_for_opdef(opdef, user_flag_vals, force)
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
    ...     choice:
    ...       default: a
    ...       choices: [a, b, c]
    ... """)

    >>> opdef = gf.default_model["op"]

    >>> flag_vals(opdef, {})
    {'choice': 'a'}

Invalid choice, no force:

    >>> flag_vals(opdef, {"choice": "d"})
    Traceback (most recent call last):
    InvalidFlagChoice: ('d', <guild.guildfile.FlagDef 'choice'>)

    >>> flag_vals(opdef, {"choice": "d"}, force=True)
    {'choice': 'd'}

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

Opdef with invalid default (Guild doesn't validate):

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
    {'float': 'abc'}

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
