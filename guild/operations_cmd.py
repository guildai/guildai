import click

import guild.click_util

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
@guild.click_util.use_args

def operations(ctx, args):
    """Show model operations.
    """
    import guild.operations_cmd_impl
    guild.operations_cmd_impl.main(args, ctx)
