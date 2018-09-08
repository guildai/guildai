# Operations

Operation support is implemented by the `op` module:

    >>> import guild.op

For our tests, we'll use a helper function that returns an instance of
`guild.guildfile.OpDef`:

    >>> from guild import guildfile

    >>> def OpDef(main, name="op"):
    ...   data = [
    ...     {
    ...       "model": "model",
    ...       "operations": {
    ...         name: {
    ...           "main": main
    ...         }
    ...       }
    ...     }
    ...   ]
    ...   gf = guildfile.Guildfile(data, "<string>")
    ...   return gf.models["model"].get_operation(name)

We'll also create a helper function that returns and instance of
`guild.op.Operation` given arguments to `OpDef` above:

    >>> def Operation(*args, **kw):
    ...   model = None # not used
    ...   return guild.op.Operation(model, OpDef(*args, **kw))

Note that the `"test"` argument is an operation reference, which is
not used in our tests.

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

Main modules cannot be empty:

    >>> Operation(main="")
    Traceback (most recent call last):
    InvalidMain: ('', 'missing command spec')

## Flag args

Flags are defined in guildfiles (defaults) and also provided as
command line arguments to the run command. `_flag_args` returns a list
of command line arg for a map of flag values.

We'll create a helper function to get the args:

    >>> class FlagDefProxy(object):
    ...
    ...   def __init__(self, name, choices=None, arg_name=None,
    ...                arg_skip=False):
    ...     self.name = name
    ...     self.choices = [
    ...       ChoiceProxy(**choice) for choice in (choices or [])
    ...     ]
    ...     self.arg_name = arg_name
    ...     self.arg_skip = arg_skip

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
    ...         if name in ["choices", "arg_name", "arg_skip"]
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

If a flag value is True, the flag will be listed a flag option.

    >>> flag_args({"test": True, "batch-size": 50})
    ['--batch-size', '50', '--test']

We can modify the argument name:

    >>> flag_args({"batch-size": {"value": 50, "arg_name": "batch_size"}})
    ['--batch_size', '50']

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

    >>> out, _ = gapi.run("test", cwd=pre_process_project, run_dir=run_dir)
    >>> print(out)
    abcdef: ABCDEF
    abcxyz: ABCXYZ

Let's confirm that our run directory contains the expected files:

    >>> dir(run_dir)
    ['.guild', 'abcdef', 'abcxyz']

    >>> cat(join_path(run_dir, "abcdef"))
    ABCDEF

    >>> cat(join_path(run_dir, "abcxyz"))
    ABCXYZ
