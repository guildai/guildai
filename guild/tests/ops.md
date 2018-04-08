# Operations

Operation support is implemented by the `op` module:

    >>> import guild.op

For our tests, we'll use a helper function that returns an instance of
`guild.guildfile.OpDef`:

    >>> import guild.guildfile

    >>> def OpDef(cmd, name="op"):
    ...     data = [
    ...       {
    ...         "model": "model",
    ...         "operations": {
    ...           name: {
    ...             "cmd": cmd
    ...           }
    ...         }
    ...       }
    ...     ]
    ...     gf = guild.guildfile.Guildfile(data, "<string>")
    ...     return gf.models["model"].get_operation(name)

We'll also create a helper function that returns and instance of
`guild.op.Operation` given arguments to `OpDef` above:

    >>> def Operation(*args, **kw):
    ...     model = None # not used
    ...     return guild.op.Operation(model, OpDef(*args, **kw))

Note that the `"test"` argument is an operation reference, which is
not used in our tests.

## Command specs

Command specs are used to generate Python commands. The first part of
the spec is used as the Python script or module. It can be a module
name with or without a py extension.

Here's an operation with a simple "train" cmd:

    >>> op = Operation(cmd="train")
    >>> op.cmd_args
    ['...python...', '-um', 'guild.op_main', 'train']

NOTE: The above formatting, with the line feed after '-u' is required
when running tests in Python 3. The regex that formats unicode refs as
strings is fooled by the example. We need to break the line as a work
around.

Command specs may contain additional arguments, which will be included
in the Python command.

    >>> op = Operation(cmd="train epoch=10 tags='tag1 tag2'")
    >>> op.cmd_args
    ['...python...', '-um', 'guild.op_main', 'train', 'epoch=10',
     'tags=tag1 tag2']

NOTE: The above formatting, with the line feed after '-u' is required
when running tests in Python 3. The regex that formats unicode refs as
strings is fooled by the example. We need to break the line as a work
around.

Command specs cannot be empty:

    >>> Operation(cmd="")
    Traceback (most recent call last):
    InvalidCmd

## Flag args

Flags are defined in guildfiles (defaults) and also provided as
command line arguments to the run command. `_flag_args` returns a list
of command line arg for a map of flag values.

We'll create a helper function to get the args:

    >>> class FlagDefProxy(object):
    ...
    ...     def __init__(self, name, choices=None, arg_name=None,
    ...                  arg_skip=False):
    ...         self.name = name
    ...         self.choices = [
    ...             ChoiceProxy(**choice) for choice in (choices or [])
    ...         ]
    ...         self.arg_name = arg_name
    ...         self.arg_skip = arg_skip

    >>> class ChoiceProxy(object):
    ...
    ...     def __init__(self, value=None, args=None):
    ...         self.value = value
    ...         self.args = args

    >>> class OpDefProxy(object):
    ...
    ...     def __init__(self, flags):
    ...         self._flags = flags
    ...
    ...     def flag_values(self):
    ...         return {
    ...             name: self._flag_val(flag)
    ...             for name, flag in self._flags.items()
    ...         }
    ...
    ...     def _flag_val(self, flag):
    ...         try:
    ...             return flag["value"]
    ...         except TypeError:
    ...             return flag
    ...
    ...     def get_flagdef(self, name):
    ...         flag = self._flags[name]
    ...         if isinstance(flag, dict):
    ...             flagdef_args = {
    ...                 name: flag[name] for name in flag
    ...                 if name in ["choices", "arg_name", "arg_skip"]
    ...             }
    ...             return FlagDefProxy(name, **flagdef_args)
    ...         else:
    ...             return FlagDefProxy(name)

    >>> def flag_args(flags, cmd_args=None):
    ...     from guild import util
    ...     cmd_args = cmd_args or []
    ...     opdef = OpDefProxy(flags)
    ...     resolved_flag_vals = util.resolve_all_refs(opdef.flag_values())
    ...     flags, _flag_map = guild.op._flag_args(
    ...         resolved_flag_vals,
    ...         opdef,
    ...         cmd_args)
    ...     return flags

Empty flags:

    >>> flag_args({})
    []

Single flag:

    >>> flag_args({"epochs": 100})
    ['--epochs', '100']

Multiple flags are returned in sorted order:

    >>> flag_args({"epochs": 100, "data": "my-data"})
    ['--data', 'my-data', '--epochs', '100']

If a flag value is None, the flag will not be included as an option.

    >>> flag_args({"test": None, "batch-size": 50})
    ['--batch-size', '50']

If a flag value is True, the flag will be listed a flag option.

    >>> flag_args({"test": True, "batch-size": 50})
    ['--batch-size', '50', '--test']

We can modify the argument name:

    >>> flag_args({"batch-size": {"value": 50, "arg_name": "batch_size"}})
    ['--batch_size', '50']

The second argument to the `_flag_args` function is a list of command
arguments. The function uses this list to check for shadowed flags. A
shadowed flag is a flag that is defined directly in the operation
`cmd` spec as an option. Guild prevents redefining command options
with flags.

Consider an operation definition that looks like this:

    operation:
      train:
        cmd: train --epochs=100

The cmd arg in this case are:

    >>> cmd_args = ["train", "--epochs=1000"]

Given this cmd, `_flag_args` prevents the `epochs` option from being
redefined and logs a warning. Let's capture output to verify.

    >>> log_capture = LogCapture()
    >>> with log_capture:
    ...   flag_args({"epochs": 100, "batch-size": 50}, cmd_args)
    ['--batch-size', '50']

    >>> log_capture.print_all()
    WARNING: ignoring flag 'epochs = 100' because it's shadowed in the operation cmd

Flags args may contain references to flags.

    >>> flag_args({"a": 1, "b": "b-${a}"})
    ['--a', '1', '--b', 'b-1']

### Flag choices

Flag choices can be used for two purposes:

- Limit available flag values
- Define additional arguments for a command

In the simple case, we're just defining the set of legal values. This
doesn't effect the generated arguments.

    >>> flag_args({
    ...     "color": {
    ...         "value": "blue",
    ...         "choices": []
    ...      }
    ... })
    ['--color', 'blue']

We can however use choice `args` to modify the arguments:

    >>> flag_args({
    ...     "color": {
    ...          "value": "blue",
    ...          "choices": [{"value": "blue",
    ...                       "args": {"hex": "00f",
    ...                                "rgb": "0,0,255"}}]
    ...     }
    ... })
    ['--color', 'blue', '--hex', '00f', '--rgb', '0,0,255']

We can use `arg_skip` to omit the choice value:

    >>> flag_args({
    ...     "color": {
    ...          "value": "blue",
    ...          "arg_skip": True,
    ...          "choices": [{"value": "blue",
    ...                       "args": {"hex": "00f",
    ...                                "rgb": "0,0,255"}}]
    ...     }
    ... })
    ['--hex', '00f', '--rgb', '0,0,255']

## Command args

Command args are created using `_cmd_args`. These are simply parsed
parts from a command string. However, like flag values, command args
may contain references to flag values.

    >>> guild.op._cmd_args([], {})
    []

    >>> guild.op._cmd_args(["foo", "--bar"], {})
    ['foo', '--bar']

    >>> guild.op._cmd_args(["foo", "--a=${a}"], {"a": 1})
    ['foo', '--a=1']

    >>> guild.op._cmd_args(["foo", "--a=${a}"], {"a": "foo-${b}-bar", "b": 2})
    ['foo', '--a=foo-2-bar']

## Operation flags

Operation flags may be defined in two places:

- Within the operation itself
- Within the operation model

Flags defined in the operation override flags defined in the model.

For our tests we'll use the train operation:

    >>> opdef = OpDef("train")

We can get the flags defined for this op using the `all_flag_values`
method:

    >>> opdef.flag_values()
    {}

Our sample operations aren't initialized with any flags, so we expect
this list to be empty.

Let's add some flags, starting with the operation model. We'll use the
`set_flag_value` method:

    >>> opdef.modeldef.set_flag_value("epochs", 100)

And now enumerate flag values for the operation:

    >>> opdef.flag_values()
    {'epochs': 100}

Let's define the same flag at the operation level:

    >>> opdef.set_flag_value("epochs", 200)
    >>> opdef.flag_values()
    {'epochs': 200}

Here are a couple additional flags, one defined in the model and the
other in the operations:

    >>> opdef.set_flag_value("batch-size", 50)
    >>> opdef.modeldef.set_flag_value("learning-rate", 0.1)
    >>> pprint(opdef.flag_values())
    {'batch-size': 50,
     'epochs': 200,
     'learning-rate': 0.1}
