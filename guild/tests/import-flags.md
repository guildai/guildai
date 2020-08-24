# Import flags

Flags can be imported from a main module by using the special
`$import` attribute of the operation flags.

We'll use the sample project `flags`:

    >>> project_dir = sample("projects", "flags")

Load the guild file:

    >>> with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...           "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...     gf = guildfile.for_dir(project_dir, no_cache=True)

Ref to the default model:

    >>> m = gf.default_model

Helper to return flags for an operation:

    >>> def flags(op_name):
    ...     return m[op_name].flags

Helper function to print flag attributes.

    >>> def flag_info(op_name, flag_name):
    ...     op = m[op_name]
    ...     flag = op.get_flagdef(flag_name)
    ...     if flag.description:
    ...         print("description: {}".format(flag.description))
    ...     if flag.choices:
    ...         print("choices: {}".format([c.value for c in flag.choices]))
    ...     print("default: {}".format(flag.default))

Helper to print flag values:

    >>> def flag_vals(op_name):
    ...     pprint(m[op_name].flag_values())

Helper for flags dest:

    >>> def flags_dest(op_name):
    ...     print(m[op_name].flags_dest)

## Default flags

As of 0.7, Guild no longer automatically imports flags.

Flags for `default-args`:

    >>> flags("default-args")
    []

    >>> flag_vals("default-args")
    {}

Guild still detects the flags interface even when flags aren't
imported.

    >>> flags_dest("default-args")
    args

For `default-globals`:

    >>> flags("default-globals")
    []

    >>> flag_vals("default-globals")
    {}

    >>> flags_dest("default-globals")
    globals

## Import all available flags

Flags for `import-all-args`:

    >>> flags("import-all-args")
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

    >>> flags("import-all-globals")
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

    >>> flags("args-flags")
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

    >>> flags("globals-flags")
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

    >>> flags("import-all-args-with-mods")
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

    >>> flags("import-all-globals-with-mods")
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

    >>> flags("explicit-args")
    [<guild.guildfile.FlagDef 'foo'>]

    >>> flag_info("explicit-args", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_vals("explicit-args")
    {'foo': 1}

Similarly for `explicit-globals`:

    >>> flags("explicit-globals")
    [<guild.guildfile.FlagDef 'f_str'>]

    >>> flag_info("explicit-globals", "f_str")
    default: hi

    >>> flag_vals("explicit-globals")
    {'f_str': 'hi'}

## Disabling imports

Imports can be disabled by specifying `no` or `[]` for `flags-import`:

    >>> flags("no-imports-1")
    []

    >>> flags("no-imports-2")
    []

`no-imports-3` disables imports and then defines its own flags:

    >>> flags("no-imports-3")
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

    >>> flags("all-imports-1")
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flags("all-imports-2")
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_int'>,
     <guild.guildfile.FlagDef 'f_str'>]

## Implicit imports

If `flags-import` is not specified, Guild implicitly imports flags
defined in config.

    >>> flags("implicit-imports")
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

    >>> flags("implicit-imports-2")
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

    >>> flags("skip-imports")
    [<guild.guildfile.FlagDef 'f_bool'>,
     <guild.guildfile.FlagDef 'f_float'>,
     <guild.guildfile.FlagDef 'f_str'>]

    >>> flags("skip-imports-2")
    [<guild.guildfile.FlagDef 'bar'>]

## Alt argparse usage

The module `main_args2` - used by the `import-all-args2` operation -
has a different argparse usage.

    >>> flags("import-all-args2")
    [<guild.guildfile.FlagDef 'bar'>, <guild.guildfile.FlagDef 'foo'>]

## Marge based on arg-name

    >>> flags("merge-by-arg-name")
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

## Error decoding flags

If Guild can't serialize argparse defined values as JSON, it prints a
warning message and coerces the value to a string.

    >>> project_dir = sample("projects", "flags-2")

    >>> with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...           "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...     with LogCapture() as logs:
    ...         gf = guildfile.for_dir(project_dir, no_cache=True)

    >>> logs.print_all()
    WARNING: [import_flags_main] cannot serialize value <object object at ...>
    for flag foo - coercing to string

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'json-decodable'>]

    >>> op = gf.default_model.get_operation("json-decodable")
    >>> op.flags
    [<guild.guildfile.FlagDef 'foo'>]

    >>> op.get_flagdef("foo").default
    '<object object at ...>'

## Arg parsers that use parents

    >>> flags("parser-parents")
    [<guild.guildfile.FlagDef 'a'>,
     <guild.guildfile.FlagDef 'b'>,
     <guild.guildfile.FlagDef 'c'>]

    >>> flag_info("parser-parents", "a")
    default: A

    >>> flag_info("parser-parents", "b")
    default: B

    >>> flag_info("parser-parents", "c")
    default: C

    >>> flag_vals("parser-parents")
    {'a': 'A', 'b': 'B', 'c': 'C'}

## Module errors

The tests below show how Guild handles module errors when trying to
import flags.

### Missing module with `argparse`

Use gapi to show error messages when importing flags.

    >>> project_dir = sample("projects", "flags")

Helper:

    >>> def help_op(op, **kw):
    ...     out = gapi.run_capture_output(
    ...         op, help_op=True, cwd=project_dir, **kw)
    ...     print(out)

When Guild imports flags for a module that imports `argparse`, it runs
the module with `--help`. In this case, any missing modules generate
an error.

For Python 2:

    >>> help_op("import_error_args.py")  # doctest: -PY3
    WARNING: cannot import flags from ./import_error_args.py: ImportError:
    No module named xxx_not_a_valid_module (run with guild --debug for details)
    Usage: guild run [OPTIONS] import_error_args.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

For Python 3 (not including 3.5):

    >>> help_op("import_error_args.py")  # doctest: -PY2 -PY35
    WARNING: cannot import flags from ./import_error_args.py: ModuleNotFoundError:
    No module named 'xxx_not_a_valid_module' (run with guild --debug for details)
    Usage: guild run [OPTIONS] import_error_args.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

Guild hides the details to avoid generating noise when a required
module isn't available. This is common when examining a project from
outside an activated environment. While we want to show a warning, we
don't want to flood the output with the applicable traceback.

We can get the traceback by running with the debug option. We use
`LOG_LEVEL=10` env var in this case.

For Python 2:

    >>> help_op("import_error_args.py", debug=True)  # doctest: -PY3
    ???
    WARNING: cannot import flags from ./import_error_args.py: ImportError:
    No module named xxx_not_a_valid_module
    ERROR: [import_flags_main] loading module from './import_error_args.py'
    Traceback (most recent call last):
      ...
      File "./import_error_args.py", line 2, in <module>
        import xxx_not_a_valid_module
    ImportError: No module named xxx_not_a_valid_module
    ...
    Usage: guild run [OPTIONS] import_error_args.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

For Python 3 (not including 3.5):

    >>> help_op("import_error_args.py", debug=True)  # doctest: -PY2 -PY35
    ???
    WARNING: cannot import flags from ./import_error_args.py: ModuleNotFoundError:
    No module named 'xxx_not_a_valid_module'
    ERROR: [import_flags_main] loading module from './import_error_args.py'
    Traceback (most recent call last):
      ...
      File "./import_error_args.py", line 2, in <module>
        import xxx_not_a_valid_module
    ModuleNotFoundError: No module named 'xxx_not_a_valid_module'
    ...
    Usage: guild run [OPTIONS] import_error_args.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

### Missing module with globals

Guild does not execute a module if it doesn't import `argparse`. It
looks at the module AST to find flag candidates. For this reason a
missing module does not register as a warning.

    >>> help_op("import_error_globals.py")
    Usage: guild run [OPTIONS] import_error_globals.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.

### Synax error

Guild cannot even inspect a module with a syntax error.

    >>> help_op("syntax_error.py")
    WARNING: cannot import flags from ./syntax_error.py: invalid syntax on line 1
      foo bar
            ^
    Usage: guild run [OPTIONS] syntax_error.py [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
