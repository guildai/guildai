# Run ops

When an operation is run, the module `guild.commands.run_impl`
resolves the command line specification to an instance of
`guild.operation.Op`, which is used to both preview the operation and
also to run the operation.

These tests look at this behavior by running various module functions.

    >>> from guild.commands import run_impl

We'll be testing functions with parsed command line arguments, so
we'll need a helper.

    >>> from guild import click_util
    >>> from guild.commands import run as run_cmd

    >>> def parse_args(args):
    ...     ctx = run_cmd.run.make_context("test", args)
    ...     return click_util.Args(**ctx.params), ctx

Here's an example of parsing run args:

    >>> args, _ctx = parse_args(["train", "lr=0.1", "--yes"])
    >>> args.opspec
    u'train'

    >>> args.flags
    (u'lr=0.1',)

    >>> args.yes
    True

For the tests below, we'll call `run_impl._resolve_model_op` with
various combinations of parsed arguments within a temp working
directory to control what the run command sees.

Here's the working directory:

    >>> cwd = mkdtemp()

And the helper function:

    >>> def resolve_model_op(opspec):
    ...     with Chdir(cwd):
    ...         return run_impl._resolve_model_op(opspec)

Before running any tests, we need to pre-emptively load Guild plugins
as the act of changing the cwd while processing op specs will cause
spurious error messages when plugins are loaded for the op resolution
process. (Not sure why this is, but no matter - this step resolves the
issue.)

    >>> from guild import plugin
    >>> list(plugin.iter_plugins())
    [...]

## Bad op specs

The tests below illustrate various invalid operation specs.

To control our test context, we'll use a new directory:

    >>> cwd = mkdtemp()

Running a non-existing operation with no model spec:

    >>> resolve_model_op("train")
    Traceback (most recent call last):
    SystemExit: ("cannot find operation train\nYou may need
    to include a model in the form MODEL:OPERATION. Try
    'guild operations' for a list of available operations.", 1)

Running a non-existing operation with a model spec:

    >>> resolve_model_op("__no_exists__:train")
    Traceback (most recent call last):
    SystemExit: (..."cannot find a model matching '__no_exists__'\nTry
    'guild models' for a list of available models.", 1)

## Op for a Python script

Let's create an empty Python script in the working directory and
specify it as the op spec.

    >>> write(join_path(cwd, "train.py"), "")

We'll resolve the operation, capturing any warnings:

    >>> with LogCapture() as log:
    ...     model, op_name = resolve_model_op("train.py")
    >>> model
    <guild.plugins.python_script.PythonScriptModelProxy ...>
    >>> op_name
    'train.py'
    >>> model.modeldef.name
    ''
    >>> model.modeldef.operations
    [<guild.guildfile.OpDef 'train.py'>]

Ignore any warnings:

    >>> logs = log.get_all()
    >>> assert (not logs or
    ...         len(logs) == 1 and
    ...         logs[0].getMessage().startswith(
    ...            "cannot import flags from train.py")), logs

## Op for a shell script

Here's a shell script:

    >>> train_sh = join_path(cwd, "train.sh")
    >>> write(train_sh, "")

The resolved model before making the script to executable:

    >>> resolve_model_op("train.sh")
    Traceback (most recent call last):
    SystemExit: ("cannot find operation train.sh\nYou may need to include
    a model in the form MODEL:OPERATION. Try 'guild operations'
    for a list of available operations.", 1)

Let's make the script executable:

    >>> import stat
    >>> os.chmod(train_sh, os.stat(train_sh).st_mode | stat.S_IEXEC)

And resolve again:

    >>> model, op_name = resolve_model_op("train.sh")
    >>> model
    <guild.plugins.exec_script.ExecScriptModelProxy ...>
    >>> op_name
    'train.sh'
    >>> model.modeldef.name
    ''
    >>> model.modeldef.operations
    [<guild.guildfile.OpDef 'train.sh'>]

## Op for batch spec

The special characeter '+' indicates that the operation should be a
batch run.

    >>> resolve_model_op("+")
    (<guild.model_proxy.BatchModelProxy ...>, '+')
