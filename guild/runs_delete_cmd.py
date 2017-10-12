import click

import guild.click_util
import guild.runs_cmd_support

@click.command("delete, rm", help="""
Delete one or more runs.

%s

If a RUN is not specified, assumes all runs (i.e. as if ':' was
specified).
""" % guild.runs_cmd_support.RUN_ARG_HELP)
@click.argument("runs", metavar="[RUN...]",  nargs=-1)
@guild.runs_cmd_support.run_scope_options
@guild.runs_cmd_support.run_filters
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
