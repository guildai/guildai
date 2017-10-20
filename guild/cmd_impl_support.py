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

import os

import guild.cli
import guild.click_util
import guild.model
import guild.modelfile

def init_model_path(args, ctx):
    if not args.all:
        guild.model.set_path([])
    _try_add_model_source(ctx)

def _try_add_model_source(ctx):
    maybe_model_source = _find_model_source(cwd(ctx))
    if maybe_model_source:
        guild.model.add_model_source(maybe_model_source)

def cwd(ctx):
    return ctx.obj["cwd"]

def _find_model_source(path):
    # Note that the order of NAMES matters as the first match is used
    # over subsequent names.
    for name in guild.modelfile.NAMES:
        filename = os.path.join(path, name)
        if os.path.isfile(filename):
            return filename
    return None

def iter_models(args, ctx):
    init_model_path(args, ctx)
    models = list(guild.model.iter_models())
    if not models:
        no_models_error(ctx)
    return models

def _handle_no_models(args):
    if args.all:
        guild.cli.out(
            "There are no models installed on this system.")
    else:
        guild.cli.out(
            "There are no models defined in this directory.\n"
            "Try a different directory or specify --all to list all "
            "installed models.")
    guild.cli.error()

def iter_all_models(ctx):
    _try_add_model_source(ctx)
    return guild.model.iter_models()

def modelfile(ctx):
    try:
        return guild.modelfile.from_dir(cwd(ctx))
    except (guild.modelfile.NoModels, IOError):
        no_models_error(ctx)

def no_models_error(ctx):
    guild.cli.error(
        "%s does not contain any models\n"
        "Try a different directory or '%s' for more information."
        % (cwd_desc(ctx), guild.click_util.cmd_help(ctx)))

def cwd_desc(ctx):
    cwd_ = cwd(ctx)
    if os.path.abspath(cwd_) == os.path.abspath(os.getcwd()):
        return "this directory"
    else:
        return "'%s'" % cwd_

def is_cwd_model(model, ctx):
    return (
        model.package_name[0] == '.' and
        (os.path.abspath(model.package_name[0])
         == os.path.abspath(cwd(ctx))))
