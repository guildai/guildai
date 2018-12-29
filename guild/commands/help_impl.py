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

import click

import guild.help

from guild import cmd_impl_support

class Pkg(object):
    """Local structure representing a model package."""

    def __init__(self, name, guildfile):
        self.name = name
        self.guildfile = guildfile

def main(args, ctx):
    gf = cmd_impl_support.path_or_package_guildfile(args.path_or_package, ctx)
    desc = _guildfile_desc(gf)
    help = _format_guildfile_help(gf, desc, args)
    _print_help(help, args)

def _guildfile_desc(gf):
    pkg = gf.package
    if pkg is None:
        return None
    return "the '%s' package" % pkg.name

def _format_guildfile_help(guildfile, desc, args):
    if args.package_description:
        return guild.help.package_description(guildfile)
    else:
        return guild.help.guildfile_console_help(guildfile, desc)

def _print_help(help, args):
    if args.no_pager:
        click.echo(help)
    else:
        click.echo_via_pager(help)
