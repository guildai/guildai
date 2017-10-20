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

from guild import cli
from guild import package
from guild.cmd_impl_support import init_model_path
from guild.model import iter_models

def main(args, ctx):
    init_model_path(ctx, args.all)
    formatted = [_format_model(m) for m in iter_models()]
    if not formatted:
        _handle_no_models(args)
    cli.table(
        sorted(formatted, key=lambda m: m["fullname"]),
        cols=["fullname", "description"],
        detail=(["name", "source", "operations"] if args.verbose else [])
    )

def _format_model(model):
    modeldef = model.modeldef
    return {
        "fullname": _format_fullname(model),
        "name": modeldef.name,
        "source": modeldef.modelfile.src,
        "description": modeldef.description or "",
        "operations": ", ".join([op.name for op in modeldef.operations])
    }

def _format_fullname(model):
    return package.apply_namespace(model.fullname)

def _handle_no_models(args):
    if args.all:
        cli.out("There are no models installed on this system.")
    else:
        cli.out(
            "There are no models defined in this directory.\n"
            "Try a different directory or specify --all to list all "
            "installed models.")
    cli.error()
