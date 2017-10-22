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

import guild.model

from guild import cli
from guild import cmd_impl_support
from guild import model_util
from guild import util

def main(args, ctx):
    cmd_impl_support.init_model_path(ctx, args.all, "--all")
    formatted = [_format_op(op, model) for op, model in _iter_ops()]
    filtered = [op for op in formatted if _filter_op(op, args)]
    cli.table(
        sorted(filtered, key=lambda m: m["fullname"]),
        cols=["fullname", "description"],
        detail=(["name", "model", "cmd"] if args.verbose else [])
    )

def _iter_ops():
    for model in guild.model.iter_models():
        for op in model.modeldef.operations:
            yield op, model

def _format_op(op, model):
    model_fullname = model_util.model_fullname(model)
    return {
        "fullname": "%s:%s" % (model_fullname, op.name),
        "description": op.description or "",
        "model": model_fullname,
        "name": op.name,
        "cmd": op.cmd,
    }

def _filter_op(op, args):
    filter_vals = [
        op["fullname"],
        op["description"],
    ]
    return util.match_filter(args.filters, filter_vals)
