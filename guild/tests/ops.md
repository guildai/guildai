# Operations

Operation support is implemented by the `op` module:

    >>> import guild.op

For our tests, we'll use a helper function that returns an instance of
`guild.guildfile.OpDef`:

    >>> def OpDef(main, name="op", extra_data=None, gf_src=None):
    ...   op_data = {
    ...     "main": main
    ...   }
    ...   op_data.update(extra_data or {})
    ...   data = [
    ...     {
    ...       "model": "model",
    ...       "operations": {
    ...         name: op_data
    ...       }
    ...     }
    ...   ]
    ...   gf = guildfile.Guildfile(data, gf_src or "<string>")
    ...   return gf.models["model"].get_operation(name)

We'll also create a helper function that returns and instance of
`guild.op.Operation` given arguments to `OpDef` above:

    >>> def Operation(*args, **kw):
    ...   opdef = OpDef(*args, **kw)
    ...   opdef.set_modelref((None, None, None, None))
    ...   return guild.op.Operation(opdef)

Note that the `"test"` argument is an operation reference, which is
not used in our tests.

## Representing an operation as data

Before looking at other operation attributes, let's look at an
operation as data.

    >>> op = Operation(main="test")
    >>> pprint(op.opdef.as_data())
    {'main': 'test'}

## Command specs

Command specs are used to generate Python commands. The first part of
the spec is used as the Python script or module. It can be a module
name with or without a py extension.

Here's an operation that uses the "train" main module:

    >>> op = Operation(main="train")
    >>> op.cmd_args
    ['...python...', '-um', 'guild.op_main', 'train']

NOTE: The above formatting, with the line feed after '-u' is required
when running tests in Python 3. The regex that formats unicode refs as
strings is fooled by the example. We need to break the line as a work
around.

Command specs may contain additional arguments, which will be included
in the Python command.

    >>> op = Operation(main="train epoch=10 tags='tag1 tag2'")
    >>> op.cmd_args
    ['...python...', '-um', 'guild.op_main', 'train', 'epoch=10',
     'tags=tag1 tag2']

NOTE: The above formatting, with the line feed after '-u' is required
when running tests in Python 3. The regex that formats unicode refs as
strings is fooled by the example. We need to break the line as a work
around.

## Flag args

Flags are defined in guildfiles (defaults) and also provided as
command line arguments to the run command. `_flag_args` returns a list
of command line arg for a map of flag values.

We'll create a helper function to get the args:

    >>> class FlagDefProxy(object):
    ...
    ...   def __init__(self, name, choices=None, arg_name=None,
    ...                arg_skip=False, arg_switch=None,
    ...                allow_other=False):
    ...     self.name = name
    ...     self.choices = [
    ...       ChoiceProxy(**choice) for choice in (choices or [])
    ...     ]
    ...     self.arg_name = arg_name
    ...     self.arg_skip = arg_skip
    ...     self.arg_switch = arg_switch
    ...     self.allow_other = allow_other

    >>> class ChoiceProxy(object):
    ...
    ...   def __init__(self, value=None, args=None):
    ...     self.value = value
    ...     self.args = args

    >>> class OpDefProxy(object):
    ...
    ...   def __init__(self, flags):
    ...     self._flags = flags
    ...
    ...   def flag_values(self):
    ...     return {
    ...       name: self._flag_val(flag)
    ...       for name, flag in self._flags.items()
    ...     }
    ...
    ...   def _flag_val(self, flag):
    ...     try:
    ...       return flag["value"]
    ...     except TypeError:
    ...       return flag
    ...
    ...   def get_flagdef(self, name):
    ...     flag = self._flags[name]
    ...     if isinstance(flag, dict):
    ...       flagdef_args = {
    ...         name: flag[name] for name in flag
    ...         if name not in ("value")
    ...       }
    ...       return FlagDefProxy(name, **flagdef_args)
    ...     else:
    ...       return FlagDefProxy(name)

    >>> def flag_args(flags, cmd_args=None):
    ...   from guild import util
    ...   cmd_args = cmd_args or []
    ...   opdef = OpDefProxy(flags)
    ...   resolved_flag_vals = util.resolve_all_refs(opdef.flag_values())
    ...   flags, _flag_map = guild.op._flag_args(
    ...     resolved_flag_vals,
    ...     opdef,
    ...     cmd_args)
    ...   return flags

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

If a flag value is boolean, it will be rendered as its string
representation:

    >>> flag_args({"test": True, "batch-size": 50})
    ['--batch-size', '50', '--test', 'True']

    >>> flag_args({"test": False, "batch-size": 50})
    ['--batch-size', '50', '--test', 'False']

### Flag arg switches

A flag may specify an arg switch, which will be used to determine if
the flag option is used as an option switch--i.e. an option without a
value.

Here's a case where arg value is set to True and the corresponding
value is also True.

    >>> flag_args({"legacy": {"value": True, "arg_switch": True}})
    ['--legacy']

If the flag value is different from a non-None arg value, it won't
appear in the arg list.

    >>> flag_args({"legacy": {"value": False, "arg_switch": True}})
    []

Here we'll switch the logic and use an arg value of False:

    >>> flag_args({"not-legacy": {"value": False, "arg_switch": False}})
    ['--not-legacy']

    >>> flag_args({"not-legacy": {"value": True, "arg_switch": False}})
    []

When arg value is None, an arg value is passed through:

    >>> flag_args({"not-legacy": {"value": True, "arg_switch": None}})
    ['--not-legacy', 'True']

Values are compared using Python's `==` operator. In some cases this
might lead to a surprising result. Here we'll compare 1 and True:

    >>> flag_args({"legacy": {"value": 1, "arg_switch": True}})
    ['--legacy']

But "1" is not equal to True:

    >>> flag_args({"legacy": {"value": "1", "arg_switch": True}})
    []

Here are cases using string values:

    >>> flag_args({"legacy": {"value": "yes", "arg_switch": "yes"}})
    ['--legacy']

    >>> flag_args({"no-legacy": {"value": "no", "arg_switch": "no"}})
    ['--no-legacy']


### Using a different argument name

We can modify the argument name by specifying `arg_name`:

    >>> flag_args({"batch-size": {"value": 50, "arg_name": "batch_size"}})
    ['--batch_size', '50']

### Shadowed flag values

The second argument to the `_flag_args` function is a list of command
arguments. The function uses this list to check for shadowed flags. A
shadowed flag is a flag that is defined directly in the operation
`main` spec as an option. Guild prevents redefining command options
with flags.

Consider an operation definition that looks like this:

    operation:
      train:
        main: train --epochs=100

The cmd args in this case are:

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
    ...   "color": {
    ...     "value": "blue",
    ...     "choices": []
    ...    }
    ... })
    ['--color', 'blue']

We can however use choice `args` to modify the arguments:

    >>> flag_args({
    ...   "color": {
    ...      "value": "blue",
    ...      "choices": [{"value": "blue",
    ...                   "args": {"hex": "00f",
    ...                            "rgb": "0,0,255"}}]
    ...   }
    ... })
    ['--color', 'blue', '--hex', '00f', '--rgb', '0,0,255']

We can use `arg_skip` to omit the choice value:

    >>> flag_args({
    ...   "color": {
    ...      "value": "blue",
    ...      "arg_skip": True,
    ...      "choices": [{"value": "blue",
    ...                   "args": {"hex": "00f",
    ...                            "rgb": "0,0,255"}}]
    ...   }
    ... })
    ['--hex', '00f', '--rgb', '0,0,255']

Choices are generally used to validate user-specified values. If we
specified a value that isn't a valid choice, Guild logs a warning.

    >>> flag_args({
    ...   "color": {
    ...     "value": "white",
    ...     "choices": [{"value": "blue"}]
    ...   }
    ... })
    ['--color', 'white']

We can indicate that the flag supports other values:

    >>> with LogCapture() as log:
    ...   flag_args({
    ...     "color": {
    ...       "value": "white",
    ...       "allow_other": True,
    ...       "choices": [{"value": "blue"}]
    ...     }
    ...   })
    ['--color', 'white']

The log:

    >>> log.get_all()
    []

It's possible that the list of args associated with a choice overlaps
with args provided by another flag. In this case, the value provided
by the other flag takes precendence.

    >>> flag_args({
    ...   "color": {
    ...     "value": "white"
    ...   },
    ...   "color-profile": {
    ...     "value": "light",
    ...     "arg_skip": True,
    ...     "choices": [{"value": "light",
    ...                  "args": {"color": "tan"}}
    ...     ]
    ...   }
    ... })
    ['--color', 'white']

It's possible that two flags provide the same argument. In this case,
the flag whose name has the highest ordinal string value is used:

    >>> flag_args({
    ...   "color1": {
    ...     "value": "blue",
    ...     "arg_name": "color"
    ...   },
    ...   "color2": {
    ...     "value": "red",
    ...     "arg_name": "color"
    ...   }
    ... })
    ['--color', 'red']

## Command args

Command args are created using `_split_and_resolve_args`. These are
simply parsed parts from a command string. However, like flag values,
command args may contain references to flag values.

    >>> guild.op._split_and_resolve_args([], {})
    []

    >>> guild.op._split_and_resolve_args("", {})
    []

    >>> guild.op._split_and_resolve_args(["foo", "--bar"], {})
    ['foo', '--bar']

    >>> guild.op._split_and_resolve_args("foo --bar", {})
    ['foo', '--bar']

    >>> guild.op._split_and_resolve_args(["foo", "--a=${a}"], {"a": 1})
    ['foo', '--a=1']

    >>> guild.op._split_and_resolve_args("foo --a=${a}", {"a": 1})
    ['foo', '--a=1']

    >>> guild.op._split_and_resolve_args(
    ...    ["foo", "--a=${a}"], {"a": "foo-${b}-bar", "b": 2})
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

Let's add some flags:

    >>> opdef.set_flag_value("epochs", 200)
    >>> opdef.flag_values()
    {'epochs': 200}

## Pre-processing

An operation may define a pre-process command that is run before the
operation itself is run. Unlike the operation, the pre-process command
is a shell script.

To illustrate, we'll run an operation that pre-processes a sample text
file using sed.

Here's the project and its contents:

    >>> pre_process_project = sample("projects/pre-process")

    >>> dir(pre_process_project, ignore=["*.pyc", "__pycache__"])
    ['abcdef', 'guild.yml', 'main.py']

The project provides one model 'sample' with an operation 'test':

    >>> gf = guildfile.from_dir(pre_process_project)

    >>> gf.models
    {'sample': <guild.guildfile.ModelDef 'sample'>}

    >>> gf.models["sample"].operations
    [<guild.guildfile.OpDef 'sample:test'>]

The test operation runs the main module:

    >>> test_op = gf.models["sample"].operations[0]
    >>> test_op.main
    'main'

The main module prints the contents of two files:

    >>> cat(join_path(pre_process_project, "main.py"))
    from __future__ import print_function
    <BLANKLINE>
    for name in ("abcdef", "abcxyz"):
        print("%s: %s" % (name, open(name, "r").read().rstrip()))

Each file is assumed to be in the run directory (i.e. the current
directory). 'abcdef' is resolved as a 'sample-file' resource source:

    >>> test_op.dependencies
    [<guild.guildfile.OpDependency 'sample-file'>]

    >>> gf.models["sample"].resources
    [<guild.guildfile.ResourceDef 'sample-file'>]

    >>> gf.models["sample"].resources[0].sources
    [<guild.resourcedef.ResourceSource 'file:abcdef'>]

    >>> cat(join_path(pre_process_project, "abcdef"))
    ABCDEF

'abcxyz' is generated by a pre-processing command associated with the
test operation:

    >>> test_op.pre_process
    'sed s/DEF/XYZ/ < abcdef > abcxyz'

This command is run after the operation dependencies are resolved and
before the operation itself is started.

Let's show this in action by running the test operation.

First we need a run directory:

    >>> run_dir = mkdtemp()
    >>> dir(run_dir)
    []

And we'll use gapi to run the test operation:

    >>> output = gapi.run_capture_output(
    ...   "test", cwd=pre_process_project, run_dir=run_dir)
    >>> print(output)
    Run directory is '...' (results will not be visible to Guild)
    Resolving sample-file dependency
    abcdef: ABCDEF
    abcxyz: ABCXYZ

Let's confirm that our run directory contains the expected files:

    >>> dir(run_dir)
    ['.guild', 'abcdef', 'abcxyz']

    >>> cat(join_path(run_dir, "abcdef"))
    ABCDEF

    >>> cat(join_path(run_dir, "abcxyz"))
    ABCXYZ

### Op command env

Operations configure the process environment with various values. The
env init behavior is implemented by `op._init_cmd_env`.

Here's a function that prints the various values set by
`_init_cmd_env`. It uses `OpDef` above, which is named 'op' and
defined in a model named 'model'.

    >>> def opdef_env(data, to_print=None):
    ...   import os
    ...   from guild.op import _init_cmd_env
    ...   opdef = OpDef("test", extra_data=data, gf_src="sample/guild.yml")
    ...   env = _init_cmd_env(opdef, None)
    ...   to_print = to_print or (
    ...     "GUILD_HOME",
    ...     "GUILD_OP",
    ...     "GUILD_PLUGINS",
    ...     "LOG_LEVEL",
    ...     "PYTHONPATH",
    ...     "SCRIPT_DIR",
    ...     "CMD_DIR",
    ...     "MODEL_DIR",
    ...     "MODEL_PATH",
    ...     "SET_TRACE",
    ...     "HANDLE_KEYBOARD_INTERRUPT",
    ...   )
    ...   for name in to_print:
    ...     val = env.get(name)
    ...     if val is not None:
    ...       val = val.replace(os.getcwd(), "<cwd>")
    ...     print("%s: %s" % (name, val))

Here are values for an empty op:

    >>> opdef_env({})
    GUILD_HOME: ...
    GUILD_OP: model:op
    GUILD_PLUGINS: ...
    LOG_LEVEL: 20
    PYTHONPATH: <cwd>/sample:...
    SCRIPT_DIR:
    CMD_DIR: <cwd>
    MODEL_DIR: sample
    MODEL_PATH: <cwd>/sample
    SET_TRACE: None
    HANDLE_KEYBOARD_INTERRUPT: None

`PYTHONPATH` can be prepended to using `python-path`.

    >>> opdef_env({"python-path": "foo"}, ["PYTHONPATH"])
    PYTHONPATH: <cwd>/sample/foo:...

Additional env may be provided using `env`:

    >>> opdef_env({"env": {"foo": "FOO", "bar": "BAR"}}, ["foo", "bar"])
    foo: FOO
    bar: BAR

`set_trace` and `handle_keyboard_interrupt`:

    >>> opdef_env(
    ...   {"set-trace": True,
    ...    "handle-keyboard-interrupt": True},
    ...   ["SET_TRACE", "HANDLE_KEYBOARD_INTERRUPT"])
    SET_TRACE: 1
    HANDLE_KEYBOARD_INTERRUPT: 1
