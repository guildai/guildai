# Copyright 2017-2019 TensorHub, Inc.
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

import click

from guild import click_util

@click.command()
@click.argument("packages", metavar="PACKAGE...", nargs=-1, required=True)
@click.option(
    "-U", "--upgrade",
    help="Upgrade specified packages to the newest available version.",
    is_flag=True)
@click.option(
    "--reinstall",
    help="Resinstall the package if it's already installed. Implies --upgrade.",
    is_flag=True)
@click.option("--no-cache", help="Don't use cached packages.", is_flag=True)
@click.option("--no-deps", help="Don't install dependencies.", is_flag=True)
@click.option("--pre", help="Install pre-release versions.", is_flag=True)
@click.option(
    "--target", metavar="DIR",
    help="Install package and requirements in DIR.")

@click_util.use_args

def install(args):
    """Install one or more packages.
    """
    from . import packages_impl
    packages_impl.install_packages(args)
