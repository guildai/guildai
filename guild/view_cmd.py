import click

import guild.click_util
import guild.runs_cmd

@click.command()
@guild.runs_cmd.run_scope_options
@guild.runs_cmd.run_filters
@click.option(
    "--host",
    help="Name of host interface to listen on.")
@click.option(
    "--port",
    help="Port to listen on.",
    type=click.IntRange(0, 65535))
@click.option(
    "--refresh-interval",
    help="Refresh interval (defaults to 5 seconds).",
    type=click.IntRange(1, None),
    default=5)
@click.option(
    "-n", "--no-open",
    help="Don't open the TensorBoard URL in a brower.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def view(ctx, args):
    """Visualize runs with TensorBoard.
    """
    import guild.view_cmd_impl
    guild.view_cmd_impl.main(args, ctx)
