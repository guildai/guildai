import click

import guild.click_util

from guild.packages_delete_cmd import delete_packages
from guild.packages_info_cmd import package_info
from guild.packages_list_cmd import list_packages

class PackagesGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["delete", "rm"]:
            cmd_name = "delete, rm"
        elif cmd_name in ["list", "ls"]:
            cmd_name = "list, ls"
        return super(PackagesGroup, self).get_command(ctx, cmd_name)

@click.group(invoke_without_command=True, cls=PackagesGroup)

@click.pass_context

def packages(ctx, **kw):
    """Show or manage packages.

    If COMMAND is not specified, lists packages.
    """
    if not ctx.invoked_subcommand:
        ctx.invoke(list_packages, **kw)

packages.add_command(delete_packages)
packages.add_command(list_packages)
packages.add_command(package_info)
