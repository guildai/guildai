# Op commands

Operation commands are generated using a command template and flag
values. The `op_cmd` module is responsible for this facility.

    >>> from guild import op_cmd

Command templates specify two things:

- Command args
- Flag args

Command args are pre-parsed command arguments that may be either a
literal value or a special value `__flag_args__`. The special value
`__flag_args__` indicates the position in the command arg where
resolved flag arguments are located.

Flag args specify how flag values are applied as arguments when
included in a command at the `__flag_args__` location.

For any given command template and set of flag values, `op_cmd` can
generate a command via the `cmd_args` function. If `__flag_arg__` is
not provided as a command arg value, the command will not contain flag
arguments. If a flag value is provided that does not have a
corresponding flag arg, a default flag arg is assumed.

## Examples

Helper functions:

    >>> FlagArg = op_cmd.FlagArg
    >>> CmdTemplate = op_cmd.CmdTemplate

    >>> def cmd_args(cmd_args, flag_args, flag_vals):
    ...     template = CmdTemplate(cmd_args, flag_args)
    ...     return op_cmd.cmd_args(template, flag_vals)


Simple example:

    >>> cmd_args(
    ...     ["a", "b", "__flag_args__"],
    ...     {"c": FlagArg(arg_name="C")},
    ...     {"c": 123, "d": "abc"})
    ['a', 'b', '--C', '123', '--d', 'abc']

No flag args:

    >>> cmd_args(["a", "b"], {}, {"c": 123})
    ['a', 'b']

Mapped value args:

    >>> cmd_args(
    ...     ["__flag_args__"],
    ...     {"a": FlagArg(arg_val_map={1: ["b", "c"]})},
    ...     {"a": 1})
    ['b', 'c']

Arg switches:

    >>> cmd_args(
    ...     ["__flag_args__"],
    ...     {"a": FlagArg(arg_switch=1)},
    ...     {"a": 1})
    ['--a']

Skip args:

    >>> cmd_args(
    ...     ["__flag_args__"],
    ...     {"a": FlagArg(arg_skip=True)},
    ...     {"a": 1})
    []

## Data IO

Command templates are represented as data with `as_data` and loaded
from data with `for_data`.

Helpers:

    >>> def as_data(cmd_args, flag_args):
    ...     template = CmdTemplate(cmd_args, flag_args)
    ...     data = op_cmd.as_data(template)
    ...     template2 = op_cmd.for_data(data)
    ...     data2 = op_cmd.as_data(template2)
    ...     assert data == data2, (data, data2)
    ...     pprint(data)

Examples:

    >>> as_data([], {})
    {'cmd-args': []}

    >>> as_data(["a", "b"], {"a": FlagArg()})
    {'cmd-args': ['a', 'b']}

    >>> as_data(["a", "b"], {"a": FlagArg(arg_name="A")})
    {'cmd-args': ['a', 'b'], 'flag-args': {'a': {'arg-name': 'A'}}}

    >>> as_data(["a", "b"], {
    ...     "a": FlagArg(arg_name="A"),
    ...     "b": FlagArg(arg_val_map={1: "X", 2: "Y", "z": "Z"}),
    ...     "c": FlagArg(arg_skip=True),
    ...     "d": FlagArg(arg_switch="D"),
    ...     "e": FlagArg(arg_name="E",
    ...                  arg_val_map={"e1": 1, "e2": "2"},
    ...                  arg_skip=False,
    ...                  arg_switch="2"),
    ...     "f": FlagArg(),
    ... })
    {'cmd-args': ['a', 'b'],
     'flag-args': {'a': {'arg-name': 'A'},
                   'b': {'arg-val-map': {1: 'X', 2: 'Y', 'z': 'Z'}},
                   'c': {'arg-skip': True},
                   'd': {'arg-switch': 'D'},
                   'e': {'arg-name': 'E',
                         'arg-switch': '2',
                         'arg-val-map': {'e1': 1, 'e2': '2'}}}}
