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

import click

from guild import cli
from guild import cmd_impl_support
from guild import help as helplib


class Pkg(object):
    """Local structure representing a model package."""

    def __init__(self, name, guildfile):
        self.name = name
        self.guildfile = guildfile


def main(args, ctx):
    _check_args(args)
    gf = cmd_impl_support.path_or_package_guildfile(args.path_or_package, ctx)
    desc = _guildfile_desc(gf)
    help = _format_guildfile_help(gf, desc, args)
    _print_help(help, args)


def _check_args(args):
    if args.package_description and args.markdown:
        cli.error("--package-description and --markdown cannot both be used")


def _guildfile_desc(gf):
    pkg = gf.package
    if pkg is None:
        return None
    return "the '%s' package" % pkg.name


def _format_guildfile_help(guildfile, desc, args):
    if args.package_description:
        return helplib.package_description(guildfile)
    elif args.markdown:
        return helplib.guildfile_markdown_help(
            guildfile, args.title, args.base_heading_level
        )
    else:
        return helplib.guildfile_console_help(guildfile, desc)


def _print_help(help, args):
    if args.no_pager:
        click.echo(help)
    else:
        click.echo_via_pager(help)
