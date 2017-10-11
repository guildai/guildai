import click

import guild.click_util

@click.command()
@click.argument("packages", metavar="PACKAGE...", nargs=-1, required=True)
@click.option(
    "-U", "--upgrade",
    help="Upgrade specified packages to the newest available version.",
    is_flag=True)
@click.option(
    "--force",
    help="Install over existing packages.",
    is_flag=True)

@guild.click_util.use_args

def install(args):
    """Install one or more packages.

    Packages are installed into the Guild environment and will not
    effect other applications.
    """
    import guild.install_cmd_impl
    guild.install_cmd_impl.main(args)
