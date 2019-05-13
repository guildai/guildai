# Import flags

Flags can be imported from a main module by using the special
`$import` attribute of the operation flags.

We'll use the sample project `flags`:

    >>> project_dir = sample("projects/flags")

Load the guild file:

    >>> with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...           "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...     gf = guildfile.from_dir(project_dir, no_cache=True)

For our tests, we'll use a helper function to print flag attributes.

    >>> def flag_info(op_name, flag_name):
    ...     op = gf.models["test"][op_name]
    ...     flag = op.get_flagdef(flag_name)
    ...     if flag.description:
    ...         print("description: {}".format(flag.description))
    ...     if flag.choices:
    ...         print("choices: {}".format([c.value for c in flag.choices]))
    ...     print("default: {}".format(flag.default))

And a helper to print flag values:

    >>> def flag_vals(op_name):
    ...     pprint(gf.models["test"][op_name].flag_values())

And for flags dest:

    >>> def flags_dest(op_name):
    ...     print(gf.models["test"][op_name].flags_dest)

## Implicitly import all available flags

Flags for `implicit-args`:

    >>> gf.models["test"]["implicit-args"].flags
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

    >>> gf.models["test"]["implicit-globals"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("implicit-globals", "f_bool")
    default: False

    >>> flag_info("implicit-globals", "f_float")
    default: 7.0

    >>> flag_info("implicit-globals", "f_int")
    default: 6

    >>> flag_info("implicit-globals", "f_str")
    default: hi

    >>> flag_vals("implicit-globals")
    {'f_bool': False, 'f_float': 7.0, 'f_int': 6, 'f_str': 'hi'}

    >>> flags_dest("implicit-globals")
    globals

### Redefine defaults

Guild files can redefine default values.

Here are new defaults for `main_args`:

    >>> gf.models["test"]["implicit-args-with-mods"].flags
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

    >>> gf.models["test"]["implicit-globals-with-mods"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("implicit-globals-with-mods", "f_bool")
    default: False

    >>> flag_info("implicit-globals-with-mods", "f_float")
    description: A float
    default: 8.8

    >>> flag_info("implicit-globals-with-mods", "f_int")
    default: 6

    >>> flag_info("implicit-globals-with-mods", "f_str")
    description: A greeting
    choices: ['hi', 'hola']
    default: hola

    >>> flag_vals("implicit-globals-with-mods")
    {'f_bool': False, 'f_float': 8.8, 'f_int': 6, 'f_str': 'hola'}

## Explicit flag imports

The `explicit-args` operation uses `flags-import` to limit the
imports:

    >>> gf.models["test"]["explicit-args"].flags
    [<guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("explicit-args", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_vals("explicit-args")
    {'foo': 1}

Similarly for `explicit-globals`:

    >>> gf.models["test"]["explicit-globals"].flags
    [<guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("explicit-globals", "f_str")
    default: hi

    >>> flag_vals("explicit-globals")
    {'f_str': 'hi'}

## Disabling imports

Imports can be disabled by specifying `no` or `[]` for `flags-import`:

    >>> gf.models["test"]["no-imports-1"].flags
    []

    >>> gf.models["test"]["no-imports-2"].flags
    []

`no-imports-3` disables imports and then defines its own flags:

    >>> gf.models["test"]["no-imports-3"].flags
    [<guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("no-imports-3", "foo")
    description: New def of foo
    choices: [3, 4]
    default: 3

    >>> flag_vals("no-imports-3")
    {'foo': 3}

## Don't import specific flags

In cases where a user wants to import all flags *except* certain
flags, she can use `flags-no-import`.

    >>> gf.models["test"]["skip-imports-1"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> gf.models["test"]["skip-imports-2"].flags
    [<guild.guildfile.FlagDef 'bar'>]

## Alt argparse usage

The module `main_args2` - used by the `implicit-args2` operation - has
a different argparse usage.

    >>> gf.models["test"]["implicit-args2"].flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

## Marge based on arg-name

    >>> gf.models["test"]["merge-by-arg-name"].flags
    [<guild.guildfile.FlagDef 'f_bool2'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str2'>]

    >>> flag_info("merge-by-arg-name", "f_bool2")
    default: False

    >>> flag_info("merge-by-arg-name", "f_float")
    default: 8.0

    >>> flag_info("merge-by-arg-name", "f_int")
    default: 6

    >>> flag_info("merge-by-arg-name", "f_str2")
    default: hi2
