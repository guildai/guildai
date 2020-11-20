# Op commands

Operation commands are generated using a command template and flag
values. The `op_cmd` module is responsible for this facility.

    >>> from guild import op_cmd

Command templates specify three things:

- Command args
- Command flags
- Command env

Command args are pre-parsed command arguments that may be either a
literal value or a special value `__flag_args__`. The special value
`__flag_args__` indicates the position in the command arg where
resolved flag arguments are located.

Flag args specify how flag values are applied as arguments when
included in a command at the `__flag_args__` location.

Command env is a map of environment names to values that are included
by default in the result of `cmd_env`.

For any given command template and set of flag values, `op_cmd` can
generate a command via the `cmd_args` function. If `__flag_arg__` is
not provided as a command arg value, the command will not contain flag
arguments. If a flag value is provided that does not have a
corresponding flag arg, a default flag arg is assumed.

`op_cmd` generates an environment map using the command env and
template flag values.

## Examples

Helper functions:

    >>> CmdFlag = op_cmd.CmdFlag

    >>> def generate(cmd_args, cmd_env, cmd_flags, flag_vals, flags_dest="args"):
    ...     cmd = op_cmd.OpCmd(cmd_args, cmd_env, cmd_flags, flags_dest)
    ...     args, env = op_cmd.generate(cmd, flag_vals, resolve_params=flag_vals)
    ...     print(args)
    ...     pprint(env)

Simple example:

    >>> generate(
    ...     ["a", "b", "__flag_args__"], {},
    ...     {"c": CmdFlag(arg_name="C")},
    ...     {"c": 123, "d": "abc"})
    ['a', 'b', '--C', '123', '--d', 'abc']
    {'FLAG_C': '123', 'FLAG_D': 'abc'}

No flag args:

    >>> generate(["a", "b"], {}, {}, {"c": 123})
    ['a', 'b']
    {'FLAG_C': '123'}

Various flag values:

    >>> generate(["__flag_args__"], {}, {}, {"c": 123})
    ['--c', '123']
    {'FLAG_C': '123'}

    >>> generate(["__flag_args__"], {}, {}, {"c": "123"})
    ['--c', '123']
    {'FLAG_C': '123'}

    >>> generate(["__flag_args__"], {}, {}, {"c": ""})
    ['--c', '']
    {'FLAG_C': ''}

Boolean and None values are handled differently for "args" and
"globals" flags dest.

    >>> generate(["__flag_args__"], {}, {}, {"c": True}, "args")
    ['--c', '1']
    {'FLAG_C': '1'}

    >>> generate(["__flag_args__"], {}, {}, {"c": True}, "globals")
    ['--c', 'true']
    {'FLAG_C': '1'}

    >>> generate(["__flag_args__"], {}, {}, {"c": False}, "args")
    ['--c', '']
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {}, {}, {"c": False}, "globals")
    ['--c', 'false']
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {}, {}, {"c": None}, "args")
    []
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {}, {}, {"c": None}, "globals")
    []
    {'FLAG_C': ''}

Sort order:

    >>> generate(["__flag_args__"], {}, {}, {"a": 1, "b": 2, "c": 3, "z": 4})
    ['--a', '1', '--b', '2', '--c', '3', '--z', '4']
    {'FLAG_A': '1', 'FLAG_B': '2', 'FLAG_C': '3', 'FLAG_Z': '4'}

Arg switches:

    >>> generate(
    ...     ["__flag_args__"], {},
    ...     {"a": CmdFlag(arg_switch=1)},
    ...     {"a": 1})
    ['--a']
    {'FLAG_A': '1'}

    >>> generate(
    ...     ["__flag_args__"], {},
    ...     {"a": CmdFlag(arg_switch=1)},
    ...     {"a": 2})
    []
    {'FLAG_A': '2'}

Skip args:

    >>> generate(
    ...     ["__flag_args__"], {},
    ...     {"a": CmdFlag(arg_skip=True)},
    ...     {"a": 1})
    []
    {'FLAG_A': '1'}

Params in non-flag template:

    >>> generate(
    ...     ["${i}", "${f}", "why ${s} there"], {}, {},
    ...     {"i": 1, "f": 2.3, "s": "hello"})
    ['1', '2.3', 'why hello there']
    {'FLAG_F': '2.3', 'FLAG_I': '1', 'FLAG_S': 'hello'}

## Explicit env var names

    >>> generate([], {}, {"a": CmdFlag(env_name="A")}, {"a": 1})
    []
    {'A': '1'}

## Command env

    >>> generate([], {"A": 123}, {}, {})
    []
    {'A': '123'}

    >>> generate([], {"A": "123"}, {}, {})
    []
    {'A': '123'}

    >>> generate([], {"A": ""}, {}, {"B": ""}, "args")
    []
    {'A': '', 'FLAG_B': ''}

    >>> generate(
    ...     [], {"A": True, "B": False, "C": None}, {},
    ...     {"D": True, "E": False, "F": None}, "args")
    []
    {'A': '1', 'B': '', 'C': '', 'FLAG_D': '1', 'FLAG_E': '', 'FLAG_F': ''}

Flags override command env.

    >>> generate([], {"A": 123}, {"A": CmdFlag(env_name="A")}, {"A": 456})
    []
    {'A': '456'}

## Shadowing command args

Flags cannot redefine command options.

    >>> with LogCapture(echo_to_stdout=True):
    ...     generate(["--a", "2", "__flag_args__"], {}, {}, {"a": 1})
    WARNING: ignoring flag 'a=1' because it's shadowed in the operation cmd as --a
    ['--a', '2']
    {'FLAG_A': '1'}

This warning can be avoided by explicitly skipping the flag arg.

    >>> with LogCapture(echo_to_stdout=True):
    ...     generate(
    ...         ["--a", "2", "__flag_args__"], {},
    ...         {"a": CmdFlag(arg_skip=True)},
    ...         {"a": 1})
    ['--a', '2']
    {'FLAG_A': '1'}

## Undefined references

    >>> generate(["${invalid-ref}"], {}, {}, {})
    Traceback (most recent call last):
    UndefinedReferenceError: invalid-ref

## Data IO

Command templates are represented as data with `as_data` and loaded
from data with `for_data`.

Helpers:

    >>> def as_data(cmd_args, cmd_env, cmd_flags, flags_dest):
    ...     template = op_cmd.OpCmd(cmd_args, cmd_env, cmd_flags, flags_dest)
    ...     data = op_cmd.as_data(template)
    ...     template2 = op_cmd.for_data(data)
    ...     data2 = op_cmd.as_data(template2)
    ...     assert data == data2, (data, data2)
    ...     pprint(data)

Examples:

    >>> as_data([], {}, {}, None)
    {'cmd-args': []}

    >>> as_data(["a", "b"], {}, {"a": CmdFlag()}, None)
    {'cmd-args': ['a', 'b']}

    >>> as_data(["a", "b"], {"c": 1}, {"a": CmdFlag(arg_name="A")}, "globals")
    {'cmd-args': ['a', 'b'],
     'cmd-env': {'c': 1},
     'cmd-flags': {'a': {'arg-name': 'A'}},
     'flags-dest': 'globals'}

    >>> as_data(
    ...     ["a", "b"],
    ...     {"C": 123, "D": "456"},
    ...     { "a": CmdFlag(arg_name="A"),
    ...       "b": CmdFlag(arg_skip=True),
    ...       "c": CmdFlag(arg_switch="C"),
    ...       "d": CmdFlag(arg_name="D",
    ...                    arg_skip=False,
    ...                    arg_switch="2"),
    ...       "e": CmdFlag()},
    ...     "args")
    {'cmd-args': ['a', 'b'],
     'cmd-env': {'C': 123, 'D': '456'},
     'cmd-flags': {'a': {'arg-name': 'A'},
                   'b': {'arg-skip': True},
                   'c': {'arg-switch': 'C'},
                   'd': {'arg-name': 'D', 'arg-switch': '2'}},
     'flags-dest': 'args'}
