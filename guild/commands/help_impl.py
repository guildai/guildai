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
from guild import namespace

def main(args):
    if args.model:
        modelfile, model_desc = _modelfile_for_name(args.model)
    else:
        modelfile = _cwd_modelfile()
        model_desc = None
    refs = {
        ("Modelfile", modelfile.src)
    }
    if args.package_description:
        help = guild.help.package_description(modelfile, refs)
    else:
        help = guild.help.modelfile_console_help(modelfile, refs, model_desc)
    if args.no_pager:
        click.echo(help)
    else:
        click.echo_via_pager(help)

def _modelfile_for_name(name):
    if os.path.isdir(name):
        return _modelfile_for_dir(name)
    else:
        return _package_modelfile(name)

def _modelfile_for_dir(dir):
    try:
        return guild.modelfile.from_dir(dir), None
    except guild.modelfile.NoModels:
        cli.error("'%s' does not contain a model file")

def _package_modelfile(model_ref):
    matches = list(_iter_matching_models(model_ref))
    if len(matches) == 1:
        return matches[0].modeldef.modelfile, _package_desc(matches[0])
    if not matches:
        cli.error(
            "cannot find a model matching '%s'\n"
            "Try 'guild models' for a list."
            % model_ref)
    cli.error(
        "multiple models match '%s'\n"
        "Try again with one of these models: %s"
        % (model_ref, ", ".join([model.full_name for model in matches])))

def _package_desc(model):
    package_name = namespace.apply_namespace(model.dist.project_name)
    return "the '%s' package" % package_name

def _iter_matching_models(model_ref):
    for model in guild.model.iter_models():
        if _match_model_ref(model_ref, model):
            yield model

def _match_model_ref(model_ref, model):
    if '/' in model_ref:
        # If user includes a '/' assume it's a complete name
        return model_ref == model.fullname
    else:
        # otherwise treat as a match term
        return model_ref in model.name

def _cwd_modelfile():
    modelfile = cmd_impl_support.cwd_modelfile()
    if modelfile is None:
        cli.out(
            "No help available (%s does not contain a modelfile)"
            % cmd_impl_support.cwd_desc(),
            err=True)
        cli.error()
    return modelfile
