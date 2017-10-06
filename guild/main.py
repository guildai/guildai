import logging

import click

import guild.app
import guild.cli

guild.app.init()

class Args(object):

    def __init__(self, kw):
        for name in kw:
            setattr(self, name, kw[name])

def append_params(fn, params):
    fn.__click_params__ = getattr(fn, "__click_params__", [])
    fn.__click_params__.extend(reversed(params))

###################################################################
# Main
###################################################################

class CLIGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["operations", "ops"]:
            cmd_name = "operations, ops"
        elif cmd_name in ["tensorboard", "tb"]:
            cmd_name = "tensorboard, tb"
        return super(CLIGroup, self).get_command(ctx, cmd_name)

@click.group(cls=CLIGroup)
@click.version_option(
    version=guild.app.version(),
    prog_name="guild",
    message="%(prog)s %(version)s"
)
@click.option(
    "--info", "log_level",
    help="Log information during command.",
    flag_value=logging.INFO)
@click.option(
    "--debug", "log_level",
    help="Log more information during command.",
    flag_value=logging.DEBUG)

def cli(**kw):
    """Guild AI command line interface."""
    guild.cli.main(Args(kw))

def main():
    guild.cli.apply_main(cli)

###################################################################
# check command
###################################################################

@click.command()
@click.option(
    "-T", "--tests", "all_tests",
    help="Run Guild test suite.",
    is_flag=True)
@click.option(
    "-t", "--test", "tests",
    help="Run TEST (may be used multiple times).",
    metavar="TEST",
    multiple=True)
@click.option(
    "-s", "--no-info",
    help="Don't print info (useful when just running tests).",
    is_flag=True)
@click.option(
    "-v", "--verbose",
    help="Show check details.",
    is_flag=True)

def check(**kw):
    """Check the Guild setup.

    This command performs a number of checks and prints information
    about the Guild setup.

    You can also run the Guild test suite by specifying the --tests
    option.
    """
    import guild.check_cmd
    guild.check_cmd.main(Args(kw))

cli.add_command(check)

###################################################################
# models command
###################################################################

@click.command()
@click.option(
    "-p", "--project", "project_location",
    help="Project location (file system directory) for models.",
    metavar="LOCATION")
@click.option(
    "--installed",
    help="Show available installed packages. --project is ignore.",
    is_flag=True)
@click.option(
    "-v", "--verbose",
    help="Show model details.",
    is_flag=True)
@click.pass_context

def models(ctx, **kw):
    """Show available models.

    By default Guild will show models defined in the current directory
    (in a MODEL or MODELS file). You may use --project to specify an
    alternative project location.

    To show installed models, use the --installed option. Any location
    specified by --project, will be ignored if --installed is used.
    """
    import guild.models_cmd
    guild.models_cmd.main(Args(kw), ctx)

cli.add_command(models)

###################################################################
# operations command
###################################################################

@click.command(name="operations, ops")
@click.argument("model", required=False)
@click.option(
    "-p", "--project", "project_location",
    help="Project location (file system directory) for MODEL.",
    metavar="LOCATION")
@click.option(
    "-v", "--verbose",
    help="Show operation details.",
    is_flag=True)
@click.pass_context

def operations(ctx, **kw):
    """Show model operations.
    """
    import guild.operations_cmd
    guild.operations_cmd.main(Args(kw), ctx)

cli.add_command(operations)

###################################################################
# run command
###################################################################

def run_params(fn):
    append_params(fn, [
        click.Argument(("args",), metavar="[ARG...]", nargs=-1),
        click.Option(
            ("-p", "--project", "project_location"),
            help="Project location (file system directory) for MODEL.",
            metavar="LOCATION"),
        click.Option(
            ("--disable-plugins",),
            help="A comma separated list of plugin names to disable."),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before running operation.",
            is_flag=True),
        click.Option(
            ("--print-command",),
            help="Show the operation command and exit (does not run).",
            is_flag=True),
        click.Option(
            ("--print-env",),
            help="Show the operation environment and exit (does not run).",
            is_flag=True),
    ])
    return fn

@click.command()
@click.argument("opspec", metavar="[MODEL:]OPERATION")
@run_params

def run(**kw):
    """Run a model operation.

    By default Guild will try to run OPERATION for the default model
    defined in a project. If a project location is not specified (see
    --project option below), Guild looks for a project in the current
    directory.

    If MODEL is specified, Guild will use it instead of the default
    model defined in a project.
    """
    import guild.run_cmd
    guild.run_cmd.main(Args(kw))

cli.add_command(run)

###################################################################
# runs command
###################################################################

class RunsGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["delete", "rm"]:
            cmd_name = "delete, rm"
        elif cmd_name in ["list", "ls"]:
            cmd_name = "list, ls"
        return super(RunsGroup, self).get_command(ctx, cmd_name)

def run_scope_options(fn):
    append_params(fn, [
        click.Option(
            ("-p", "--project", "project_location"),
            help=("Project location (file system directory) for filtering "
                  "runs."),
            metavar="LOCATION"),
        click.Option(
            ("-S", "--system"),
            help=("Include system wide runs rather than limit to runs "
                  "associated with a project location. Ignores LOCATION."),
            is_flag=True)
    ])
    return fn

def run_filters(fn):
    append_params(fn, [
        click.Option(
            ("-m", "--model", "models"),
            metavar="MODEL",
            help="Include only runs for MODEL.",
            multiple=True),
        click.Option(
            ("-r", "--running", "status"),
            help="Include only runs that are still running.",
            flag_value="running"),
        click.Option(
            ("-c", "--completed", "status"),
            help="Include only completed runs.",
            flag_value="completed"),
        click.Option(
            ("-s", "--stopped", "status"),
            help=("Include only runs that exited with an error or were "
                  "terminated by the user."),
            flag_value="stopped"),
        click.Option(
            ("-e", "--error", "status"),
            help="Include only runs that exited with an error.",
            flag_value="error"),
        click.Option(
            ("-t", "--terminated", "status"),
            help="Include only runs terminated by the user.",
            flag_value="terminated"),
    ])
    return fn

def runs_list_options(fn):
    run_scope_options(fn)
    run_filters(fn)
    append_params(fn, [
        click.Option(
            ("-v", "--verbose"),
            help="Show run details.",
            is_flag=True),
        click.Option(
            ("-d", "--deleted"),
            help="Show deleted runs.",
            is_flag=True),
    ])
    return fn

@click.group(invoke_without_command=True, cls=RunsGroup)
@runs_list_options
@click.pass_context

def runs(ctx, **kw):
    """Show or manage runs.

    If COMMAND is omitted, lists run. Refer to 'guild runs list
    --help' for more information on the list command.
    """
    if not ctx.invoked_subcommand:
        ctx.invoke(list_runs, **kw)
    else:
        if _params_specified(kw):
            # TODO: It'd be nice to move kw over to the subcommand.
            guild.cli.error(
                "options cannot be listed before command ('%s')"
                % ctx.invoked_subcommand)

def _params_specified(kw):
    return any((kw[key] for key in kw))

cli.add_command(runs)

###################################################################
# runs list command
###################################################################

@click.command("list, ls")
@runs_list_options
@click.pass_context

def list_runs(ctx, **kw):
    """List runs.

    By default lists runs associated with models defined in the
    current directory, or LOCATION if specified. To list all runs, use
    the --system option.

    To list deleted runs, use the --deleted option. Note that runs are
    still limited to the specified project unless --system is
    specified.

    You may apply any of the filter options below to limit the runs
    listed.
    """
    import guild.runs_cmd
    guild.runs_cmd.list_runs(Args(kw), ctx)

runs.add_command(list_runs)

###################################################################
# runs delete command
###################################################################

RUN_ARG_HELP = """
RUN may be a run ID (or the unique start of a run ID) or a zero-based
index corresponding to a run returned by the list command. Indexes may
also be specified in ranges in the form START:END where START is the
start index and END is the end index. Either START or END may be
omitted. If START is omitted, all runs up to END are selected. If END
id omitted, all runs from START on are selected. If both START and END
are omitted (i.e. the ':' char is used by itself) all runs are selected.
"""

@click.command("delete, rm", help="""
Delete one or more runs.

%s
""" % RUN_ARG_HELP)
@click.argument("runs", metavar="RUN [RUN...]", nargs=-1, required=True)
@run_scope_options
@run_filters
@click.option(
    "-y", "--yes",
    help="Do not prompt before deleting.",
    is_flag=True)
@click.pass_context

def delete_runs(ctx, **kw):
    # Help defined in command decorator.
    import guild.runs_cmd
    guild.runs_cmd.delete_runs(Args(kw), ctx)

runs.add_command(delete_runs)

###################################################################
# runs restore command
###################################################################

@click.command("restore", help="""
Restore one or more deleted runs.

%s
""" % RUN_ARG_HELP)

@click.argument("runs", metavar="RUN [RUN...]", nargs=-1, required=True)
@run_scope_options
@run_filters
@click.option(
    "-y", "--yes",
    help="Do not prompt before restoring.",
    is_flag=True)
@click.pass_context

def restore_runs(ctx, **kw):
    # Help defined in command decorator.
    import guild.runs_cmd
    guild.runs_cmd.restore_runs(Args(kw), ctx)

runs.add_command(restore_runs)

###################################################################
# runs info command
###################################################################

@click.command("info")
@click.argument("run", required=False)
@run_scope_options
@run_filters
@click.option("--files", help="Include run files", is_flag=True)
@click.pass_context

def run_info(ctx, **kw):
    """Show run details.

    RUN must be a run ID (or the start of a run ID that uniquely
    identifies a run) or a zero-based index corresponding to the run
    as it appears in the list of filtered runs.

    By default the latest run is selected (index 0).

    EXAMPLES

    Show info for the latest run in the current project:

        guild runs info

    Show info for the latest run system wide:

        guild runs info -S

    Show info for the latest completed run in the current project:

        guild runs info -c

    Show info for run a64b1710:

        guild runs info a64b1710

    """
    import guild.runs_cmd
    guild.runs_cmd.run_info(Args(kw), ctx)

runs.add_command(run_info)

###################################################################
# shell command
###################################################################

@click.command()

def shell(**kw):
    """Start a Python shell for API experimentation.
    """
    import guild.shell_cmd
    guild.shell_cmd.main(Args(kw))

cli.add_command(shell)

###################################################################
# sources command
###################################################################

class SourcesGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["rm", "remove"]:
            cmd_name = "remove, rm"
        return super(SourcesGroup, self).get_command(ctx, cmd_name)

@click.group(invoke_without_command=True, cls=SourcesGroup)
@click.pass_context

def sources(ctx, **kw):
    """Show or manage package sources.
    """
    if not ctx.invoked_subcommand:
        import guild.sources_cmd
        guild.sources_cmd.list_sources(Args(kw))

cli.add_command(sources)

###################################################################
# sources add command
###################################################################

@click.command("add")
@click.argument("name")
@click.argument("source")
@click.pass_context

def add_source(ctx, **kw):
    """Add a package source.

    NAME must be a unique source identifier for this system. Use
    'guild sources' to show a list of configured package sources.

    SOURCE must be a GitHub repository URL or a local
    directory. GitHub repository URLs may be provided in shorthand
    using ACCOUNT/REPOSITORY. For example, the SOURCE
    'guildai/guild-packages' will be interpreted as
    'https://github.com/guildai/guild-packages'.

    Local directories must be absolute paths. Use a local directory
    will avoid having to sync with an upstream source each time a
    change is made to a package. This is useful for package
    development.
    """
    import guild.sources_cmd
    guild.sources_cmd.add_source(Args(kw), ctx)

sources.add_command(add_source)

###################################################################
# sources remove command
###################################################################

@click.command("remove, rm")
@click.argument("name")

def remove_source(**kw):
    """Remove a package source.

    Use 'guild sources' for a list of package sources.
    """
    import guild.sources_cmd
    guild.sources_cmd.remove_source(Args(kw))

sources.add_command(remove_source)

###################################################################
# train command
###################################################################

@click.command("train")
@click.argument("model", required=False)
@run_params

def train(**kw):
    """Train a model.

    Equivalent to running 'guild run [MODEL:]train [ARG...]'.

    By default MODEL is the default model for project in LOCATION.

    You may omit MODEL (i.e. for training the default model) while
    providing one or more ARG values provided the first ARG value
    contains an equals sign ('='). When specifying a switch (i.e. an
    argument that doesn't accept a value) as the first ARG, you must
    provide MODEL.

    Refer to help for the run command ('guild run --help') for more
    information.

    """
    import guild.run_cmd
    args = Args(kw)
    # MODEL is treated as an ARG if it contains an equal sign (see
    # help text above).
    if args.model and "=" in args.model:
        args.args = (args.model,) + args.args
        args.model = None
    args.opspec = "%s:train" % args.model if args.model else "train"
    guild.run_cmd.main(args)

cli.add_command(train)

###################################################################
# tensorboard command
###################################################################

@click.command("tensorboard, tb")
@run_scope_options
@click.option(
    "--host",
    help="Name of host interface to listen on.")
@click.option(
    "--port",
    help="Port to listen on.",
    type=click.IntRange(0, 65535))
@click.option(
    "--refresh-interval",
    help="TensorBoard refresh interval (defaults to 5 seconds).",
    type=click.IntRange(1, None),
    default=5)
@click.option(
    "-n", "--no-open",
    help="Don't open the TensorBoard URL in a brower.",
    is_flag=True)
@click.pass_context

def tensorboard(ctx, **kw):
    """Start TensorBoard to view runs.
    """
    import guild.tensorboard_cmd
    guild.tensorboard_cmd.main(Args(kw), ctx)

cli.add_command(tensorboard)
