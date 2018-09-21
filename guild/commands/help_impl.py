# Copyright 2017-2018 TensorHub, Inc.
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

import os

import click

import guild.help
import guild.model
import guild.plugin

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import guildfile

class Pkg(object):
    """Local structure representing a model package."""

    def __init__(self, name, guildfile):
        self.name = name
        self.guildfile = guildfile

def main(args):
    path_or_package = args.path_or_package or config.cwd()
    if os.path.isdir(path_or_package):
        guildfile = _dir_guildfile(path_or_package)
        desc = None
    else:
        guildfile, desc = _package_guildfile(path_or_package)
    help = _format_guildfile_help(guildfile, desc, args)
    _print_help(help, args)

def _dir_guildfile(dir):
    try:
        return guildfile.from_dir(dir)
    except guild.guildfile.NoModels:
        mf = _try_plugin_models(dir)
        if mf:
            return mf
        cli.out(
            "No help available (%s does not contain a model file)"
            % cmd_impl_support.cwd_desc(dir), err=True)
        cli.error()
    except guild.guildfile.GuildfileError as e:
        cli.error(str(e))

def _try_plugin_models(dir):
    models_data = []
    for _, plugin in guild.plugin.iter_plugins():
        for data in plugin.find_models(dir):
            models_data.append(data)
    if not models_data:
        return None
    return guildfile.Guildfile(models_data, dir=dir)

def _package_guildfile(ref):
    matches = _matching_packages(ref)
    if len(matches) == 1:
        return matches[0].guildfile, "the '%s' package" % matches[0].name
    if not matches:
        cli.error(
            "cannot find a model package matching '%s'\n"
            "Try 'guild models -a' for a list of models and specify a path "
            "or package name for help."
            % ref)
    cli.error(
        "multiple packages match '%s'\n"
        "Try again with one of these models: %s"
        % (ref, ", ".join([pkg.name for pkg in matches])))

def _matching_packages(ref):
    pkgs = {}
    for model in guild.model.iter_models():
        if model.reference.dist_type != "package":
            continue
        pkg = Pkg(model.reference.dist_name, model.modeldef.guildfile)
        # If exact match, return one
        if ref == pkg.name:
            return [pkg]
        # otherwise check for match in full name of model
        elif ref in model.fullname:
            pkgs[pkg.name] = pkg
    return [pkgs[name] for name in sorted(pkgs)]

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
