import click

import guild.click_util
import guild.runs_cmd_support

from guild.runs_delete_cmd import delete_runs
from guild.runs_info_cmd import run_info
from guild.runs_list_cmd import list_runs
from guild.runs_restore_cmd import restore_runs

class RunsGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["delete", "rm"]:
            cmd_name = "delete, rm"
        elif cmd_name in ["list", "ls"]:
            cmd_name = "list, ls"
        return super(RunsGroup, self).get_command(ctx, cmd_name)

@click.group(invoke_without_command=True, cls=RunsGroup)
@guild.runs_cmd_support.runs_list_options

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

runs.add_command(delete_runs)
runs.add_command(run_info)
runs.add_command(list_runs)
runs.add_command(restore_runs)
