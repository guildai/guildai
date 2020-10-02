# Copyright 2017-2020 TensorHub, Inc.
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
from guild import config
from guild import util

from .cat import cat
from .check import check
from .comment import comment
from .compare import compare
from .completion import completion
from .diff import diff
from .download import download
from .export import export
from .help import help
from .import_ import import_
from .init import init
from .install import install
from .label import label
from .ls import ls
from .models import models
from .open_ import open_
from .operations import operations
from .package import package
from .packages import packages
from .publish import publish
from .pull import pull
from .push import push
from .remote import remote
from .remotes import remotes
from .run import run
from .runs import runs
from .search import search
from .select import select
from .mark import mark
from .shell import shell
from .stop import stop
from .sync import sync
from .sys import sys
from .tag import tag
from .tensorboard import tensorboard
from .tensorflow import tensorflow
from .uninstall import uninstall
from .view import view
from .watch import watch


DEFAULT_GUILD_HOME = config.default_guild_home()


@click.group(cls=click_util.Group)
@click.version_option(
    version=guild_version(), prog_name="guild", message="%(prog)s %(version)s"
)
@click.option(
    "-C",
    "cwd",
    metavar="PATH",
    help=("Use PATH as current directory for referencing guild " "files (guild.yml)."),
    default=".",
    autocompletion=click_util.completion_dir,
)
@click.option(
    "-H",
    "guild_home",
    metavar="PATH",
    help="Use PATH as Guild home (default is {}).".format(
        util.format_dir(DEFAULT_GUILD_HOME)
    ),
    default=DEFAULT_GUILD_HOME,
    envvar="GUILD_HOME",
    autocompletion=click_util.completion_dir,
)
@click.option(
    "--debug",
    "log_level",
    help="Log more information during command.",
    flag_value=logging.DEBUG,
)
@click_util.use_args
def main(args):
    """Guild AI command line interface."""
    from . import main_impl

    main_impl.main(args)


main.add_command(cat)
main.add_command(check)
main.add_command(comment)
main.add_command(compare)
main.add_command(completion)
main.add_command(diff)
main.add_command(download)
main.add_command(export)
main.add_command(help)
main.add_command(import_)
main.add_command(init)
main.add_command(install)
main.add_command(label)
main.add_command(ls)
main.add_command(models)
main.add_command(open_)
main.add_command(operations)
main.add_command(package)
main.add_command(packages)
main.add_command(publish)
main.add_command(pull)
main.add_command(push)
main.add_command(remote)
main.add_command(remotes)
main.add_command(run)
main.add_command(runs)
main.add_command(search)
main.add_command(select)
main.add_command(mark)
main.add_command(shell)
main.add_command(stop)
main.add_command(sync)
main.add_command(sys)
main.add_command(tag)
main.add_command(tensorboard)
main.add_command(tensorflow)
main.add_command(uninstall)
main.add_command(view)
main.add_command(watch)
