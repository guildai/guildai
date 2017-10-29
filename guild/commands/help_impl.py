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

import guild.help

from guild import cli
from guild import cmd_impl_support

def main(args):
    modelfile = cmd_impl_support.cwd_modelfile()
    if modelfile is None:
        cli.out(
            "No help available (%s does not contain a modelfile)"
            % cmd_impl_support.cwd_desc(),
            err=True)
        return
    refs = {
        ("Modelfile", modelfile.src)
    }
    if args.package_description:
        help = guild.help.package_description(modelfile, refs)
    else:
        help = guild.help.modelfile_console_help(modelfile, refs)
    if args.no_pager:
        click.echo(help)
    else:
        click.echo_via_pager(help)
