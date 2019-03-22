# Run Flags

Flags are provided to runs as command line arguments in the form
`NAME=VALUE`. These, along with default values defined in the Guild
file, are used as arguments to the operation main module.

We will use the functions `_apply_flag_vals` and
`_validate_opdef_flags` in `guild.commands.run_impl` to test flag
processing behavior.

    >>> from guild.commands.run_impl import _apply_flag_vals
    >>> from guild.commands.run_impl import _validate_op_flags

Here is a test Guild file:

    >>> gf = guildfile.from_string("""
    ... - model: test
    ...   operations:
    ...     simplest:
    ...       flags:
    ...         f: null
    ...     string:
    ...       flags:
    ...         f:
    ...           type: string
    ...     required-int:
    ...       flags:
    ...         f:
    ...           description: Required int flag
    ...           required: yes
    ...           type: int
    ...     numbers:
    ...       flags:
    ...         int:
    ...           type: int
    ...         float:
    ...           type: float
    ...         number:
    ...           type: number
    ...     path:
    ...       flags:
    ...         f:
    ...           type: path
    ...     existing-path:
    ...       flags:
    ...         f:
    ...           type: existing-path
    ... """)

The function `_apply_flag_vals` mutates the operation definition,
given arguments to the `run` command. We use a helper to apply this
function to a copy of our test operation so we can reuse it for
multiple tests.

Because `_validate_op_flags` validates operation flags, we need a
proxy to comply with its interface.

    >>> class OpProxy(object):
    ...     def __init__(self, opdef):
    ...         self.opdef = opdef
    ...         self.flag_vals = opdef.flag_values()

And our helper function to validate flags:

    >>> import copy
    >>> from guild import click_util

    >>> def flags(op_name, flag_vals, force=False):
    ...     opdef_orig = gf.models["test"].get_operation(op_name)
    ...     opdef_copy = copy.deepcopy(opdef_orig)
    ...     args_proxy = click_util.Args(
    ...        force_flags=force,
    ...        optimizer=None,
    ...        random_seed=None)
    ...     with StderrCapture() as stderr:
    ...         try:
    ...             _apply_flag_vals(flag_vals, opdef_copy, args_proxy)
    ...             _validate_op_flags(OpProxy(opdef_copy))
    ...         except SystemExit as e:
    ...             if e.args[0]:
    ...                 print(e.args[0])
    ...             stderr.print()
    ...             print("<exit>")
    ...         else:
    ...             pprint(opdef_copy.flag_values())

The `simplest` operation defines the simplest possible flag `f`.

    >>> flags("simplest", {})
    {'f': None}

    >>> flags("simplest", {"f": 123})
    {'f': 123}

    >>> flags("simplest", {"f": "hello"})
    {'f': 'hello'}

The `string` operation defines a flag `f` of type 'string'.

    >>> flags("string", {})
    {'f': None}

    >>> flags("string", {"f": "hello"})
    {'f': 'hello'}

    >>> flags("string", {"f": 123})
    {'f': '123'}

    >>> flags("string", {"f": 1.123})
    {'f': '1.123'}

The `required-int` operation defines a required flag `f` of type
'int'.

    >>> flags("required-int", {})
    Operation requires the following missing flags:
    <BLANKLINE>
      f  Required int flag
    <BLANKLINE>
    Run the command again with these flags specified as NAME=VAL.
    <exit>

The `numbers` operation defines three flags: int, float, and number.

    >>> flags("numbers", {})
    {'float': None, 'int': None, 'number': None}

    >>> flags("numbers", {"int": 1, "float": 2.3, "number": 4})
    {'float': 2.3, 'int': 1, 'number': 4}

    >>> flags("numbers", {"int": 1.2})
    cannot apply 1.2 to flag 'int': invalid value for type 'int'
    <exit>

    >>> flags("numbers", {"int": "1.1"})
    cannot apply '1.1' to flag 'int': invalid value for type 'int'
    <exit>

    >>> flags("numbers", {"float": "1.1"})
    {'float': 1.1, 'int': None, 'number': None}

    >>> flags("numbers", {"number": "1"})
    {'float': None, 'int': None, 'number': 1}

    >>> flags("numbers", {"number": "1.1"})
    {'float': None, 'int': None, 'number': 1.1}

The `path` operation defines a flag `f` of type 'path'. Any relative
paths are resolved to be relative to the current directory.

    >>> flags("path", {})
    {'f': None}

    >>> with Chdir("/tmp"):
    ...   flags("path", {"f": "foo"})
    {'f': '/...tmp/foo'}

    >>> with Chdir("/tmp"):
    ...   flags("path", {"f": "/foo"})
    {'f': '/foo'}

Empty strings are not considered paths:

    >>> with Chdir("/tmp"):
    ...   flags("path", {"f": ""})
    {'f': ''}

The `existing-path` operation defines a flag `f` of type
'existing-path'. Existing paths are resolved in the same way normal
paths are but an error is generated if the specified path doesn't
exist.

    >>> flags("existing-path", {})
    {'f': None}

    >>> flags("existing-path", {"f": "/not-existing"})
    invalid value for f: /not-existing does not exist
    <exit>

Undefined flags generate an error:

    >>> flags("simplest", {"not-defined": 123})
    unsupported flag 'not-defined'
    Try 'guild run test:simplest --help-op' for a list of flags or
    use --force-flags to skip this check.
    <exit>
