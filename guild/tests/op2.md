# op2

    >>> from guild import op2 as oplib

    >>> from guild import op_cmd

## Op from opdef

Helper to print generated op command:

    >>> def gen_op_cmd(op):
    ...     args, env = oplib.generate_op_cmd(op)
    ...     print(args)
    ...     pprint(env)

Python module:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ... """)

    >>> op = oplib.for_opdef(gf.default_model["op"], {})

    >>> gen_op_cmd(op)
    ['...', '-um', 'guild.op_main', 'guild.pass', '--']
    {'GUILD_OP': 'op', 'GUILD_PLUGINS': '', 'PROJECT_DIR': ''}

Python module with args and flags:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass --foo 123 --bar
    ...   flags:
    ...     baz: 456
    ... """)

    >>> op = oplib.for_opdef(gf.default_model["op"], {})

    >>> gen_op_cmd(op)
    ['...', '-um', 'guild.op_main', 'guild.pass',
     '--foo', '123', '--bar', '--', '--baz', '456']

    ['...', '-um', 'guild.op_main', 'guild.pass', '--foo', '123', '--bar', '--']
    {'GUILD_OP': 'op', 'GUILD_PLUGINS': '', 'PROJECT_DIR': ''}

With modified flag value:

    >>> op = oplib.for_opdef(gf.default_model.get_operation("op"),
    ...                     {"baz": 789})

    >>> oplib.proc_args(op)
    ['...', '-um', 'guild.op_main', 'guild.pass',
    '--foo', '123', '--bar', '--', '--baz', '789']

With shadowing flag:

    >>> op = oplib.for_opdef(gf.default_model.get_operation("op"),
    ...                     {"foo": 321, "baz": 789})

    >>> with LogCapture(stdout=True, strip_ansi_format=True):
    ...     oplib.proc_args(op)
    WARNING: ignoring flag 'foo=321' because it's shadowed in the
    operation cmd as --foo
    ['...', '-um', 'guild.op_main', 'guild.pass',
     '--foo', '123', '--bar', '--', '--baz', '789']

Choice flags:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass --foo 123 --bar
    ...   flags:
    ...     choice:
    ...       default: a
    ...       arg-skip: yes
    ...       choices:
    ...         - value: a
    ...           flags:
    ...             a1: abc
    ...             a2: 123
    ...         - value: b
    ...           flags:
    ...             b1: 4.56
    ...             b2: True
    ...     a1:
    ...       arg-name: A1
    ... """)

    >>> opdef = gf.default_model["op"]

Args are generated from flag values provided.

    >>> op = oplib.for_opdef(opdef, {})

    >>> oplib.proc_args(op)
    ['...', '-um', 'guild.op_main', 'guild.pass',
     '--foo', '123', '--bar', '--']

Use `op_util.flag_vals_for_opdef` to apply choice flag vals:

    >>> from guild import op_util2 as op_util

    >>> op = oplib.for_opdef(opdef, op_util.flag_vals_for_opdef(opdef, {}))

    >>> oplib.proc_args(op)
    ['...', '-um', 'guild.op_main', 'guild.pass',
     '--foo', '123', '--bar', '--', '--A1', 'abc', '--a2', '123']

## Data IO

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ... """)

    >>> opdef = gf.default_model["op"]

    >>> op = oplib.for_opdef(opdef, {})

    >>> pprint(oplib.as_data(op))
