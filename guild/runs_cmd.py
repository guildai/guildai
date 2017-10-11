import click

import guild.click_util

class RunsGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["delete", "rm"]:
            cmd_name = "delete, rm"
        elif cmd_name in ["list", "ls"]:
            cmd_name = "list, ls"
        return super(RunsGroup, self).get_command(ctx, cmd_name)

def run_scope_options(fn):
    guild.click_util.append_params(fn, [
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
    guild.click_util.append_params(fn, [
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
    guild.click_util.append_params(fn, [
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

###################################################################
# runs list command
###################################################################

@click.command("list, ls")
@runs_list_options

@click.pass_context
@guild.click_util.use_args

def list_runs(ctx, args):
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
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.list_runs(args, ctx)

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

If a RUN is not specified, assumes all runs (i.e. as if ':' was
specified).
""" % RUN_ARG_HELP)
@click.argument("runs", metavar="[RUN...]",  nargs=-1)
@run_scope_options
@run_filters
@click.option(
    "-y", "--yes",
    help="Do not prompt before deleting.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def delete_runs(ctx, args):
    # Help defined in command decorator.
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.delete_runs(args, ctx)

runs.add_command(delete_runs)

###################################################################
# runs restore command
###################################################################

@click.command("restore", help="""
Restore one or more deleted runs.

%s

If a RUN is not specified, assumes all runs (i.e. as if ':' was
specified).
""" % RUN_ARG_HELP)

@click.argument("runs", metavar="RUN [RUN...]", nargs=-1, required=True)
@run_scope_options
@run_filters
@click.option(
    "-y", "--yes",
    help="Do not prompt before restoring.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def restore_runs(ctx, args):
    # Help defined in command decorator.
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.restore_runs(args, ctx)

runs.add_command(restore_runs)

###################################################################
# runs info command
###################################################################

@click.command("info")
@click.argument("run", required=False)
@run_scope_options
@run_filters
@click.option("--env", help="Include run environment", is_flag=True)
@click.option("--flags", help="Include run flags", is_flag=True)
@click.option("--files", help="Include run files", is_flag=True)

@click.pass_context
@guild.click_util.use_args

def run_info(ctx, args):
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
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.run_info(args, ctx)

runs.add_command(run_info)
