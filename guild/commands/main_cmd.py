# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import logging

import click

from guild import version as guild_version
from guild import click_util

from .check_cmd import check
from .install_cmd import install
from .operations_cmd import operations
from .models_cmd import models
from .package_cmd import package
from .packages_cmd import packages
from .run_cmd import run
from .runs_cmd import runs
from .shell_cmd import shell
from .train_cmd import train
from .uninstall_cmd import uninstall
from .view_cmd import view

class CLIGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        if cmd_name in ["operations", "ops"]:
            cmd_name = "operations, ops"
        return super(CLIGroup, self).get_command(ctx, cmd_name)

@click.group(cls=CLIGroup)
@click.version_option(
    version=guild_version(),
    prog_name="guild",
    message="%(prog)s %(version)s"
)
@click.option(
    "--debug", "log_level",
    help="Log more information during command.",
    flag_value=logging.DEBUG)

@click_util.use_args

def main(args):
    """Guild AI command line interface."""
    from . import main_cmd_impl
    main_cmd_impl.main(args)

main.add_command(check)
main.add_command(install)
main.add_command(models)
main.add_command(operations)
main.add_command(package)
main.add_command(packages)
main.add_command(run)
main.add_command(runs)
main.add_command(shell)
main.add_command(train)
main.add_command(uninstall)
main.add_command(view)
