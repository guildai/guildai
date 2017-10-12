import click

import guild.click_util

@click.command("delete, rm")
@click.argument("packages", metavar="PACKAGE...")
@click.option(
    "-y", "--yes",
    help="Do not prompt before deleting.",
    is_flag=True)

@guild.click_util.use_args

def delete_packages(args):
    """Uninstall one or more packages.

    This command is equivalent to 'guild uninstall [options]
    PACKAGE...'.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.uninstall_packages(args)
