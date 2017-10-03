import click

import guild.app
import guild.cli

guild.app.init()

###################################################################
# Main
###################################################################

class CLIGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["operations", "ops"]:
            cmd_name = "operations, ops"
        return super(CLIGroup, self).get_command(ctx, cmd_name)

@click.group(cls=CLIGroup)
@click.version_option(
    version=guild.app.version(),
    prog_name="guild",
    message="%(prog)s %(version)s"
)
@click.option("--debug", hidden=True, is_flag=True)

def cli(**kw):
    """Guild AI command line interface."""
    guild.cli.main(**kw)

def main():
    guild.cli.apply_main(cli)

class Args(object):

    def __init__(self, kw):
        for name in kw:
            setattr(self, name, kw[name])

def append_params(fn, params):
    fn.__click_params__ = getattr(fn, "__click_params__", [])
    fn.__click_params__[:0] = reversed(params)

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
    "-s", "--skip-info",
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

@click.command()
@click.argument("opspec", metavar="[MODEL:]OPERATION")
@click.argument("args", metavar="[ARG...]", nargs=-1)
@click.option(
    "-p", "--project", "project_location",
    help="Project location (file system directory) for MODEL.",
    metavar="LOCATION")
@click.option(
    "-y", "--yes",
    help="Do not prompt before running operation.",
    is_flag=True)
@click.option(
    "--noinstall",
    help="Don't attempt to install MODEL if not found.",
    is_flag=True)

def run(**kw):
    """Run a model operation.

    By default Guild will try to run OPERATION for the default model
    defined in a project. If a project location is not specified (see
    --project option below), Guild looks for a project in the current
    directory.

    If MODEL is specified, Guild will use it instead of the default
    model defined in a project.

    If MODEL is specified but cannot be found in a project, either
    because a project is not specified, is not in the current
    directory, or MODEL is not available, Guild will look for an
    installed model matching MODEL. If found, Guild will run OPERATION
    for the installed model.

    If Guild cannot find MODEL, either defined in a project or
    installed, it will prompt the user to search for and install a
    model matching MODEL. This behavior can be skipped by specifying
    the --noinstall option.

    MODEL may contain an optional repository component in the form
    REPOSITORY/NAME in cases where the model name itself is
    ambigous.

    Operations on any installed model may be run by specifying the
    fully qualified model name and its operation. Use 'guild models'
    to list installed models. If a model doesn't appear in the list of
    installed models, try 'guild search MODEL' to search for the model
    in an available package repository. You may install a model using
    'guild install'. Refer to the help for these commands for more
    information.
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

def runs_filter_options(fn):
    append_params(fn, [
        click.Option(
            ("-p", "--project", "project_location"),
            help=("Project location (file system directory) for filtering "
                  "runs."),
            metavar="LOCATION"),
        click.Option(
            ("-S", "--system"),
            help=("Apply filter runs system wide rather than limit to runs "
                  "associated with a project location. Ignores LOCATION."),
            is_flag=True),
        click.Option(
            ("-r", "--running", "status"),
            help="Show only runs that are still running.",
            flag_value="running"),
        click.Option(
            ("-c", "--completed", "status"),
            help="Show only completed runs.",
            flag_value="completed"),
        click.Option(
            ("-s", "--stopped", "status"),
            help=("Show only runs that exited with an error or were "
                  "terminated by the user."),
            flag_value="stopped"),
        click.Option(
            ("-e", "--error", "status"),
            help="Show only runs that exited with an error.",
            flag_value="error"),
        click.Option(
            ("-t", "--terminated", "status"),
            help="Show only runs terminated by the user.",
            flag_value="terminated"),
    ])
    return fn

def runs_list_options(fn):
    runs_filter_options(fn)
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

    By default lists runs for models defined in a project (equivalent
    to 'guild runs list'). For the complete list functionality, use
    the 'list' command explicitly.
    """
    if not ctx.invoked_subcommand:
        ctx.invoke(list_runs, **kw)

cli.add_command(runs)

###################################################################
# runs list command
###################################################################

@click.command("list, ls")
@runs_list_options
@click.pass_context

def list_runs(ctx, **kw):
    """List runs.

    By default lists runs for models defined in the current
    project. To specify a different project, use the --project option.

    To list all runs, specify the --all option.
    """
    import guild.runs_cmd
    guild.runs_cmd.list_runs(Args(kw), ctx)

runs.add_command(list_runs)

###################################################################
# runs delete command
###################################################################

RUN_ARG_HELP = """
RUN may be a run ID (or the unique start of a run ID) or a
zero-based index corresponding to a run returned by the list
command. Indexes may also be specified in ranges in the form
START:COUNT where START is the start index.
"""

@click.command("delete, rm", help="""
Delete one or more runs.

%s
""" % RUN_ARG_HELP)
@click.argument("runs", metavar="RUN [RUN...]", nargs=-1, required=True)
@runs_filter_options
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
Restores one or more deleted runs.

%s
""" % RUN_ARG_HELP)

@click.argument("runs", metavar="RUN [RUN...]", nargs=-1, required=True)
@runs_filter_options
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
@click.argument("args", metavar="[ARG...]", nargs=-1)
@click.option(
    "-p", "--project", "project_location",
    help="Project location (file system directory) for MODEL.",
    metavar="LOCATION"
)
@click.option(
    "-y", "--yes",
    help="Do not prompt before running operation.",
    is_flag=True)

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
