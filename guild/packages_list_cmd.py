import click

import guild.click_util

@click.command("list, ls")

@guild.click_util.use_args

def list_packages(args):
    """List installed packages.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.list_packages(args)
