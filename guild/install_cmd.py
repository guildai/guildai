import click

import guild.click_util

@click.command()
@click.argument("packages", metavar="PACKAGE...", nargs=-1, required=True)
@click.option(
    "-U", "--upgrade",
    help="Upgrade specified packages to the newest available version.",
    is_flag=True)

@guild.click_util.use_args

def install(args):
    """Install one or more packages.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.install_packages(args)
