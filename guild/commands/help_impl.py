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

import os

import click

import guild.help
import guild.model
import guild.modelfile

from guild import cli
from guild import cmd_impl_support
from guild import config

class Pkg(object):
    """Local structure representing a model package."""

    def __init__(self, name, modelfile):
        self.name = name
        self.modelfile = modelfile

def main(args):
    path_or_package = args.path_or_package or config.cwd()
    if os.path.isdir(path_or_package):
        modelfile = _dir_modelfile(path_or_package)
        desc = None
    else:
        modelfile, desc = _package_modelfile(path_or_package)
    help = _format_modelfile_help(modelfile, desc, args)
    _print_help(help, args)

def _dir_modelfile(dir):
    try:
        return guild.modelfile.from_dir(dir)
    except guild.modelfile.NoModels:
        cli.out(
            "No help available (%s does not contain a model file)"
            % cmd_impl_support.cwd_desc(dir), err=True)
        cli.error()

def _package_modelfile(ref):
    matches = _matching_packages(ref)
    if len(matches) == 1:
        return matches[0].modelfile, "the '%s' package" % matches[0].name
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
        pkg = Pkg(model.reference.dist_name, model.modeldef.modelfile)
        # If exact match, return one
        if ref == pkg.name:
            return [pkg]
        # otherwise check for match in full name of model
        elif ref in model.fullname:
            pkgs[pkg.name] = pkg
    return [pkgs[name] for name in sorted(pkgs)]

def _format_modelfile_help(modelfile, desc, args):
    refs = {
        ("Modelfile", modelfile.src)
    }
    if args.package_description:
        return guild.help.package_description(modelfile, refs)
    else:
        return guild.help.modelfile_console_help(modelfile, refs, desc)

def _print_help(help, args):
    if args.no_pager:
        click.echo(help)
    else:
        click.echo_via_pager(help)
