import logging

import click

import guild.app
import guild.click_util

from guild.check_cmd import check
from guild.install_cmd import install
from guild.operations_cmd import operations
from guild.models_cmd import models
from guild.packages_cmd import packages
from guild.run_cmd import run
from guild.runs_cmd import runs
from guild.shell_cmd import shell
from guild.train_cmd import train
from guild.view_cmd import view

class CLIGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["operations", "ops"]:
            cmd_name = "operations, ops"
        return super(CLIGroup, self).get_command(ctx, cmd_name)

@click.group(cls=CLIGroup)
@click.version_option(
    version=guild.app.version(),
    prog_name="guild",
    message="%(prog)s %(version)s"
)
@click.option(
    "--debug", "log_level",
    help="Log more information during command.",
    flag_value=logging.DEBUG)

@guild.click_util.use_args

def main(args):
    """Guild AI command line interface."""
    import guild.main_cmd_impl
    guild.main_cmd_impl.main(args)

main.add_command(check)
main.add_command(install)
main.add_command(models)
main.add_command(operations)
main.add_command(packages)
main.add_command(run)
main.add_command(runs)
main.add_command(shell)
main.add_command(train)
main.add_command(view)
