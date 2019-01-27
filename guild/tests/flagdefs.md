# Flag defs

These tests examine flag defs in more detail than in
[guildfiles.md](guildfiles.md).

Here's a helper function to parse a string into a flag def:

    >>> import yaml

    >>> def flagdef(s, name="flag"):
    ...     flagdef_data = yaml.safe_load(s)
    ...     gf_data = {
    ...         "op": {
    ...             "flags": {
    ...                 name: flagdef_data
    ...             }
    ...         }
    ...     }
    ...     gf = guildfile.Guildfile(gf_data, "<string>")
    ...     return gf.default_model.get_operation("op").get_flagdef(name)

## Simple values

The simplest possible flag definition is a value:

    >>> f = flagdef("1.123")

The value is used as the flag default:

    >>> f.default
    1.123

Other examples:

    >>> flagdef("1").default
    1

    >>> flagdef("hello").default
    'hello'

    >>> flagdef("yes").default
    True

    >>> print(flagdef("null").default)
    None

    >>> flagdef("[1,2,3]").default
    [1, 2, 3]

## Flag config

When a map is specified, map values are used to configure the flagdef.

    >>> f = flagdef("""
    ... description: A flag
    ... default: 1.0
    ... choices: [1.0, 2.0, 3.0]
    ... required: yes
    ... arg-name: f
    ... null-label: should never see this
    ... min: 1.0
    ... max: 3.0
    ... """)

    >>> f.description
    'A flag'

    >>> f.default
    1.0

    >>> f.choices
    [<guild.guildfile.FlagChoice 1.0>,
     <guild.guildfile.FlagChoice 2.0>,
     <guild.guildfile.FlagChoice 3.0>]

    >>> f.required
    True

    >>> f.arg_name
    'f'

    >>> f.null_label
    'should never see this'

    >>> f.min
    1.0

    >>> f.max
    3.0

    >>> f.extra
    {}

## Extra attributes

Uses may add additional attributes to a flag def, which will be
accessible as specified under the flagdef's `extra` attr.

Here we have a flag def with four extra attributes:

    >>> f = flagdef("""
    ... description: A sample
    ... default: 1
    ... min: 0
    ... max: 100
    ... distribution: log-normal
    ... mean: 0.0
    ... sigma: 2.0
    ... q: 1.0
    ... """)

    >>> pprint(f.extra)
    {'distribution': 'log-normal',
     'mean': 0.0,
     'q': 1.0,
     'sigma': 2.0}
