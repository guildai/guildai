import click

import guild.click_util
import guild.runs_cmd_support

@click.command("info")
@click.argument("run", required=False)
@guild.runs_cmd_support.run_scope_options
@guild.runs_cmd_support.run_filters
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
