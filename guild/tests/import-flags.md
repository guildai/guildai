# Import flags

Flags can be imported from a main module by using the special
`$import` attribute of the operation flags.

We'll use the sample project `flags`:

    >>> project_dir = sample("projects/flags")

Load the guild file:

    >>> gf = guildfile.from_dir(project_dir, no_cache=True)

For our tests, we'll use a helper function to print flag attributes.

    >>> def flag_info(op_name, flag_name):
    ...     op = gf.models["test"].get_operation(op_name)
    ...     flag = op.get_flagdef(flag_name)
    ...     if flag.description:
    ...         print("description: {}".format(flag.description))
    ...     if flag.choices:
    ...         print("choices: {}".format([c.value for c in flag.choices]))
    ...     print("default: {}".format(flag.default))

And a helper to print flag values:

    >>> def flag_vals(op_name):
    ...     pprint(gf.models["test"].get_operation(op_name).flag_values())

And for flags dest:

    >>> def flags_dest(op_name):
    ...     print(gf.models["test"].get_operation(op_name).flags_dest)

## Implicitly import all available flags

Flags for `implicit-args`:

    >>> gf.models["test"].get_operation("implicit-args").flags
    [<guild.guildfile.FlagDef 'bar'>,
     <guild.guildfile.FlagDef 'foo'>]

The import process reads flag attributes from the arg parse support in
the main module:

    >>> flag_info("implicit-args", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_info("implicit-args", "bar")
    description: Bar
    default: 0.001

    >>> flag_vals("implicit-args")
    {'bar': 0.001, 'foo': 1}

    >>> flags_dest("implicit-args")
    args

This applies equally to `implicit-globals`:

    >>> gf.models["test"].get_operation("implicit-globals").flags
    [<guild.guildfile.FlagDef 'bam'>, <guild.guildfile.FlagDef 'baz'>]

    >>> flag_info("implicit-globals", "baz")
    default: 6

    >>> flag_info("implicit-globals", "bam")
    default: 7.0

    >>> flag_vals("implicit-globals")
    {'bam': 7.0, 'baz': 6}

    >>> flags_dest("implicit-globals")
    globals

### Redefine defaults

Guild files can redefine default values.

Here are new defaults for `main_args`:

    >>> gf.models["test"].get_operation("implicit-args-with-mods").flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("implicit-args-with-mods", "foo")
    description: Foo
    choices: [1, 2]
    default: 2

    >>> flag_info("implicit-args-with-mods", "bar")
    description: Raised bar
    default: 0.001

    >>> flag_vals("implicit-args-with-mods")
    {'bar': 0.001, 'foo': 2}

And for `main_globals`:

    >>> gf.models["test"].get_operation("implicit-globals-with-mods").flags
    [<guild.guildfile.FlagDef 'bam'>,
     <guild.guildfile.FlagDef 'baz'>,
     <guild.guildfile.FlagDef 'baz2'>]

    >>> flag_info("implicit-globals-with-mods", "baz")
    default: 6

    >>> flag_info("implicit-globals-with-mods", "bam")
    description: A sound
    choices: ['pow', 'bam', 'zap']
    default: pow

    >>> flag_info("implicit-globals-with-mods", "baz2")
    description: Nuther baz
    default: 8.8

    >>> flag_vals("implicit-globals-with-mods")
    {'bam': 'pow', 'baz': 6, 'baz2': 8.8}

## Explicit flag imports

The `explicit-args` operation uses `flags-import` to limit the
imports:

    >>> gf.models["test"].get_operation("explicit-args").flags
    [<guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("explicit-args", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_vals("explicit-args")
    {'foo': 1}

Similarly for `explicit-globals`:

    >>> gf.models["test"].get_operation("explicit-globals").flags
    [<guild.guildfile.FlagDef 'bam'>]

    >>> flag_info("explicit-globals", "bam")
    default: 7.0

    >>> flag_vals("explicit-globals")
    {'bam': 7.0}

## Disabling imports

Imports can be disabled by specifying `no` or `[]` for `flags-import`:

    >>> gf.models["test"].get_operation("no-imports-1").flags
    []

    >>> gf.models["test"].get_operation("no-imports-2").flags
    []

`no-imports-3` disables imports and then defines its own flags:

    >>> gf.models["test"].get_operation("no-imports-3").flags
    [<guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("no-imports-3", "foo")
    description: New def of foo
    choices: [3, 4]
    default: 3

    >>> flag_vals("no-imports-3")
    {'foo': 3}

## Alt argparse usage

The module `main_args2` - used by the `implicit-args2` operation - has
a different argparse usage.

    >>> gf.models["test"].get_operation("implicit-args2").flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]
