import click

import guild.click_util

@click.command("info")
@click.argument("package", True)

@guild.click_util.use_args

def package_info(args):
    """Show package details.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.package_info(args)
