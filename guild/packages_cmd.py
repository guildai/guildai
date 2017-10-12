import click

import guild.click_util

class PackagesGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["uninstall", "rm"]:
            cmd_name = "uninstall, rm"
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

###################################################################
# packages list command
###################################################################

@click.command("list, ls")

@guild.click_util.use_args

def list_packages(args):
    """List installed packages.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.list_packages(args)

packages.add_command(list_packages)
