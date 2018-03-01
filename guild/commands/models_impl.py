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

from guild import cli
from guild import cmd_impl_support
from guild import model
from guild import util

def main(args):
    cmd_impl_support.init_model_path(args)
    formatted = [_format_model(m) for m in model.iter_models()]
    filtered = [m for m in formatted if _filter_model(m, args)]
    cli.table(
        sorted(filtered, key=lambda m: m["fullname"]),
        cols=["fullname", "description"],
        detail=(["source", "operations", "details"] if args.verbose else [])
    )

def _format_model(model):
    modeldef = model.modeldef
    description, details = util.split_description(modeldef.description)
    return {
        "fullname": model.fullname,
        "name": modeldef.name,
        "source": modeldef.guildfile.src,
        "description": description,
        "details": details,
        "operations": ", ".join([op.name for op in modeldef.operations])
    }

def _filter_model(model, args):
    filter_vals = [
        model["fullname"],
        model["description"],
    ]
    return util.match_filters(args.filters, filter_vals)
