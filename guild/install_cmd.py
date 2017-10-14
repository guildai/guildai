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

import click

import guild.click_util

@click.command()
@click.argument("packages", metavar="PACKAGE...", nargs=-1, required=True)
@click.option(
    "-U", "--upgrade",
    help="Upgrade specified packages to the newest available version.",
    is_flag=True)

@guild.click_util.use_args

def install(args):
    """Install one or more packages.
    """
    import guild.packages_cmd_impl
    guild.packages_cmd_impl.install_packages(args)
