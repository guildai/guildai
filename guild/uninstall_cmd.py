import click

import guild.click_util

@click.command()
@click.argument("packages", metavar="PACKAGE...", nargs=-1, required=True)

@guild.click_util.use_args

def uninstall(args):
    """Uninstall one or more packages.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.uninstall_packages(args)
