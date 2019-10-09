# op2

    >>> from guild import op2 as oplib

    >>> from guild import op_cmd

## Op from opdef

Python module:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass
    ... """)

    >>> op = oplib.for_opdef(gf.default_model.get_operation("op"), {})
    >>> pprint(op_cmd.as_data(op.cmd_template))
    {'cmd-args': ['${python_exe}',
                  '-um',
                  'guild.op_main',
                  'guild.pass',
                  '--',
                  '__flag_args__']}

    >>> oplib.proc_args(op)
    ['...', '-um', 'guild.op_main', 'guild.pass', '--']

Python module with args and flags:

    >>> gf = guildfile.for_string("""
    ... op:
    ...   main: guild.pass --foo 123 --bar
    ...   flags:
    ...     baz: 456
    ... """)

    >>> op = oplib.for_opdef(gf.default_model.get_operation("op"), {})

    >>> oplib.proc_args(op)
    ['...', '-um', 'guild.op_main', 'guild.pass',
     '--foo', '123', '--bar', '--', '--baz', '456']
