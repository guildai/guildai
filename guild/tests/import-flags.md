# Import flags

Flags can be imported from a main module by using the special
`$import` attribute of the operation flags.

We'll use the sample project `flags`:

    >>> project_dir = sample("projects/flags")

For our tests, we'll use a helper function to print flag attributes.

    >>> def flag_info(gf, op_name, flag_name):
    ...     op = gf.models["test"].get_operation(op_name)
    ...     flag = op.get_flagdef(flag_name)
    ...     print("description: {}".format(flag.description))
    ...     if flag.choices:
    ...         print("choices: {}".format([c.value for c in flag.choices]))
    ...     print("default: {}".format(flag.default))

Load the guild file:

    >>> gf = guildfile.from_dir(project_dir, no_cache=True)

Flags for `import-1`:

    >>> gf.models["test"].get_operation("import-1").flags
    [<guild.guildfile.FlagDef 'bar'>,
     <guild.guildfile.FlagDef 'foo'>]

The import process reads flag attributes from the arg parse support in
the main module:

    >>> flag_info(gf, "import-1", "foo")
    description: Foo
    choices: [1, 2]
    default: 1

    >>> flag_info(gf, "import-1", "bar")
    description: Bar
    default: 0.001

The `import-2` operation defines an imported flag. Imports don't
overwrite defined flag attributes.

    >>> gf.models["test"].get_operation("import-2").flags
    [<guild.guildfile.FlagDef 'bar'>,
     <guild.guildfile.FlagDef 'foo'>]

In this case, the flag 'foo' is defined with a default value of 2. The
imported value of 1 (see above) is not applied but the description is:

    >>> flag_info(gf, "import-2", "foo")
    description: Foo
    choices: [1, 2]
    default: 2

The 'bar' flag is imported in its entirety:

    >>> flag_info(gf, "import-2", "bar")
    description: Bar
    default: 0.001

The `import-3` operation defines 'foo' and only imports 'bar':

    >>> gf.models["test"].get_operation("import-3").flags
    [<guild.guildfile.FlagDef 'bar'>,
     <guild.guildfile.FlagDef 'foo'>]

    >>> flag_info(gf, "import-3", "foo")
    description:
    choices: [1, 2, 3]
    default: 3

    >>> flag_info(gf, "import-3", "bar")
    description: Bar
    default: 0.001

The `import-4` operation uses a different module, `main2`, which
defines its arg parser in a function `_init_args`, which is called
only when then module is run as '__main__'. Otherwise, `import-4` is
the same as `import-1` in that it imports both 'foo' and 'bar flags
without defining any flags itself.

    >>> flag_info(gf, "import-4", "foo")
    description: Foo
    default: 1

    >>> flag_info(gf, "import-4", "bar")
    description: Bar
    default: 0.001
