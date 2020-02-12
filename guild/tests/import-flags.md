# Import flags

Flags can be imported from a main module by using the special
`$import` attribute of the operation flags.

We'll use the sample project `flags`:

    >>> project_dir = sample("projects", "flags")

Load the guild file:

    >>> with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...           "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...     gf = guildfile.for_dir(project_dir, no_cache=True)

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

## Default flags

As of 0.7, Guild no longer automatically imports flags.

Flags for `default-args`:

    >>> gf.models["test"]["default-args"].flags
    []

    >>> flag_vals("default-args")
    {}

Guild still detects the flags interface even when flags aren't
imported.

    >>> flags_dest("default-args")
    args

For `default-globals`:

    >>> gf.models["test"]["default-globals"].flags
    []

    >>> flag_vals("default-globals")
    {}

    >>> flags_dest("default-globals")
    globals

## Import all available flags

Flags for `import-all-args`:

    >>> gf.models["test"]["import-all-args"].flags
    [<guild.guildfile.FlagDef 'bar'>,
     <guild.guildfile.FlagDef 'foo'>]

The import process reads flag attributes from the arg parse support in
the main module:

    >>> flag_info("import-all-args", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_info("import-all-args", "bar")
    description: Bar
    default: 0.001

    >>> flag_vals("import-all-args")
    {'bar': 0.001, 'foo': 1}

    >>> flags_dest("import-all-args")
    args

This applies to `import-all-globals`:

    >>> gf.models["test"]["import-all-globals"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("import-all-globals", "f_bool")
    default: False

    >>> flag_info("import-all-globals", "f_float")
    default: 7.0

    >>> flag_info("import-all-globals", "f_int")
    default: 6

    >>> flag_info("import-all-globals", "f_str")
    default: hi

    >>> flag_vals("import-all-globals")
    {'f_bool': False, 'f_float': 7.0, 'f_int': 6, 'f_str': 'hi'}

    >>> flags_dest("import-all-globals")
    globals

### Define new flags

`args-flags`:

    >>> gf.models["test"]["args-flags"].flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

Guild implicitly imports info for defined flags when `flags-import` is
not specified.

    >>> flag_info("args-flags", "foo")
    description: Foo
    choices: [1, 2]
    default: 2

    >>> flag_info("args-flags", "bar")
    description: Raised bar
    default: 0.001

    >>> flag_vals("args-flags")
    {'bar': 0.001, 'foo': 2}

And for `globals-flags`:

    >>> gf.models["test"]["globals-flags"].flags
    [<guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("globals-flags", "f_float")
    description: A float
    default: 8.8

    >>> flag_info("globals-flags", "f_str")
    description: A greeting
    choices: ['hi', 'hola']
    default: hola

    >>> flag_vals("globals-flags")
    {'f_float': 8.8, 'f_str': 'hola'}

### Redefine defaults

Guild files can redefine default values.

`import-all-args-with-mods`:

    >>> gf.models["test"]["import-all-args-with-mods"].flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("import-all-args-with-mods", "foo")
    description: Foo
    choices: [1, 2]
    default: 2

    >>> flag_info("import-all-args-with-mods", "bar")
    description: Raised bar
    default: 0.001

    >>> flag_vals("import-all-args-with-mods")
    {'bar': 0.001, 'foo': 2}

And for `main_globals`:

    >>> gf.models["test"]["import-all-globals-with-mods"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("import-all-globals-with-mods", "f_bool")
    default: False

    >>> flag_info("import-all-globals-with-mods", "f_float")
    description: A float
    default: 8.8

    >>> flag_info("import-all-globals-with-mods", "f_int")
    default: 6

    >>> flag_info("import-all-globals-with-mods", "f_str")
    description: A greeting
    choices: ['hi', 'hola']
    default: hola

    >>> flag_vals("import-all-globals-with-mods")
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

## Importing all flags

By default, Guild imports all detected flags. However, this behavior
can be made explicit in the Guild file.

`all-imports` and `all-imports-2` both indicate that all flags should
be imported.

    >>> gf.models["test"]["all-imports-1"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> gf.models["test"]["all-imports-2"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

## Implicit imports

If `flags-import` is not specified, Guild implicitly imports flags
defined in config.

    >>> gf.models["test"]["implicit-imports"].flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

Each flag imports attributes from the module.

    >>> flag_info("implicit-imports", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_info("implicit-imports", "bar")
    description: Bar
    default: 0.001

The first variant uses `flags-import-skip` to skip import of 'bar'.

    >>> gf.models["test"]["implicit-imports-2"].flags
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("implicit-imports-2", "foo")
    description: Foo
    choices: [1, 2]
    default: 2

    >>> flag_info("implicit-imports-2", "bar")
    default: 0.1

## Don't import specific flags

In cases where a user wants to import all flags *except* certain
flags, she can use `flags-import-skip`.

    >>> gf.models["test"]["skip-imports"].flags
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> gf.models["test"]["skip-imports-2"].flags
    [<guild.guildfile.FlagDef 'bar'>]

## Alt argparse usage

The module `main_args2` - used by the `import-all-args2` operation -
has a different argparse usage.

    >>> gf.models["test"]["import-all-args2"].flags
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
