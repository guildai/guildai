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
`__flag_args__` indicates the position in the command arg list where
resolved flag arguments occur.

Flag args specify how flag values are applied as arguments when
included in a command at the `__flag_args__` location.

Command env is a map of environment names to values that are included
by default in the result of `cmd_env`.

For any given command template and set of flag values, `op_cmd` can
generate a command via the `cmd_args` function. If `__flag_arg__` is
not provided as a command arg value, the command will not contain flag
arguments. If a flag value is provided that does not have a
corresponding flag arg, that flag value is not included in the list of
generated arguments.

`op_cmd` generates an environment map using the command env and
template flag values.

## Examples

Helper functions:

    >>> CmdFlag = op_cmd.CmdFlag

    >>> def generate(cmd_args, flag_vals, cmd_flags=None, cmd_env=None, dest="args"):
    ...     # If cmd_flags is not specified, use defaults for flag vals
    ...     cmd_flags = cmd_flags if cmd_flags is not None else {
    ...         name: CmdFlag() for name in flag_vals}
    ...     cmd_env = cmd_env or {}
    ...     cmd = op_cmd.OpCmd(cmd_args, cmd_env, cmd_flags, dest)
    ...     args, env = op_cmd.generate_op_args_and_env(
    ...         cmd, flag_vals, resolve_params=flag_vals)
    ...     print(args)
    ...     pprint(env)

Simple example:

    >>> generate(
    ...     ["a", "b", "__flag_args__"],
    ...     {"c": 123, "d": "abc"},
    ...     {"c": CmdFlag(arg_name="C"), "d": CmdFlag()})
    ['a', 'b', '--C', '123', '--d', 'abc']
    {'FLAG_C': '123', 'FLAG_D': 'abc'}

No flag args:

    >>> generate(["a", "b"], {"c": 123})
    ['a', 'b']
    {'FLAG_C': '123'}

Various flag values:

    >>> generate(["__flag_args__"], {"c": 123})
    ['--c', '123']
    {'FLAG_C': '123'}

    >>> generate(["__flag_args__"], {"c": "123"})
    ['--c', '123']
    {'FLAG_C': '123'}

    >>> generate(["__flag_args__"], {"c": ""})
    ['--c', '']
    {'FLAG_C': ''}

Boolean and None values are handled differently for "args" and
"globals" flags dest.

    >>> generate(["__flag_args__"], {"c": True}, dest="args")
    ['--c', '1']
    {'FLAG_C': '1'}

    >>> generate(["__flag_args__"], {"c": True}, dest="globals")
    ['--c', 'true']
    {'FLAG_C': '1'}

    >>> generate(["__flag_args__"], {"c": False}, dest="args")
    ['--c', '']
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {"c": False}, dest="globals")
    ['--c', 'false']
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {"c": None}, dest="args")
    []
    {'FLAG_C': ''}

    >>> generate(["__flag_args__"], {"c": None}, dest="globals")
    []
    {'FLAG_C': ''}

Sort order:

    >>> generate(["__flag_args__"], {"a": 1, "b": 2, "c": 3, "z": 4})
    ['--a', '1', '--b', '2', '--c', '3', '--z', '4']
    {'FLAG_A': '1', 'FLAG_B': '2', 'FLAG_C': '3', 'FLAG_Z': '4'}

Arg switches:

    >>> generate(
    ...     ["__flag_args__"],
    ...     {"a": 1},
    ...     {"a": CmdFlag(arg_switch=1)})
    ['--a']
    {'FLAG_A': '1'}

    >>> generate(
    ...     ["__flag_args__"],
    ...     {"a": 2},
    ...     {"a": CmdFlag(arg_switch=1)})
    []
    {'FLAG_A': '2'}

Skip args:

    >>> generate(
    ...     ["__flag_args__"],
    ...     {"a": 1},
    ...     {"a": CmdFlag(arg_skip=True)})
    []
    {'FLAG_A': '1'}

Params in non-flag template:

    >>> generate(
    ...     ["${i}", "${f}", "why ${s} there"],
    ...     {"i": 1, "f": 2.3, "s": "hello"})
    ['1', '2.3', 'why hello there']
    {'FLAG_F': '2.3', 'FLAG_I': '1', 'FLAG_S': 'hello'}

Arg encoding:

    >>> generate(
    ...     ["__flag_args__"],
    ...     {"b1": True, "b2": False},
    ...     {"b1": CmdFlag(arg_encoding={True: "yes", False: "no"}),
    ...      "b2": CmdFlag(arg_encoding={True: "yes", False: "no"})})
    ['--b1', 'yes', '--b2', 'no']
    {'FLAG_B1': 'yes', 'FLAG_B2': 'no'}

Env encoding:

    >>> generate(
    ...     ["__flag_args__"],
    ...     {"b1": True, "b2": False},
    ...     {"b1": CmdFlag(env_encoding={True: "ON", False: "OFF"}),
    ...      "b2": CmdFlag(env_encoding={True: "ON", False: "OFF"})})
    ['--b1', '1', '--b2', '']
    {'FLAG_B1': 'ON', 'FLAG_B2': 'OFF'}


## Explicit env var names

    >>> generate([], {"a": 1}, {"a": CmdFlag(env_name="A")})
    []
    {'A': '1'}

## Command env

    >>> generate([], {}, cmd_env={"A": 123})
    []
    {'A': '123'}

    >>> generate([], {}, cmd_env={"A": "123"})
    []
    {'A': '123'}

    >>> generate([], {"B": ""}, cmd_env={"A": ""}, dest="args")
    []
    {'A': '', 'FLAG_B': ''}

    >>> generate(
    ...     [], {"D": True, "E": False, "F": None},
    ...     cmd_env={"A": True, "B": False, "C": None},
    ...     dest="args")
    []
    {'A': '1', 'B': '', 'C': '', 'FLAG_D': '1', 'FLAG_E': '', 'FLAG_F': ''}

Flags override command env.

    >>> generate([], {"A": 456}, {"A": CmdFlag(env_name="A")}, cmd_env={"A": 123})
    []
    {'A': '456'}

## Shadowing command args

Flags cannot redefine command options.

    >>> with LogCapture(echo_to_stdout=True):
    ...     generate(["--a", "2", "__flag_args__"], {"a": 1})
    WARNING: ignoring flag 'a=1' because it's shadowed in the operation cmd as --a
    ['--a', '2']
    {'FLAG_A': '1'}

This warning can be avoided by explicitly skipping the flag arg.

    >>> with LogCapture(echo_to_stdout=True):
    ...     generate(
    ...         ["--a", "2", "__flag_args__"],
    ...         {"a": 1},
    ...         {"a": CmdFlag(arg_skip=True)})
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
    {'cmd-args': ['a', 'b'], 'cmd-flags': {'a': {}}}

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
                   'd': {'arg-name': 'D', 'arg-switch': '2'},
                   'e': {}},
     'flags-dest': 'args'}
