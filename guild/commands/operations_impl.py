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

from __future__ import absolute_import
from __future__ import division

from guild import cli
from guild import cmd_impl_support
from guild import util

from guild.commands import models_impl

def main(args):
    cmd_impl_support.init_model_path()
    gf_dirs, filters = cmd_impl_support.guildfile_dirs(args.filters)
    formatted = [_format_op(op, model) for op, model in _iter_ops(gf_dirs)]
    filtered = [op for op in formatted if _filter_op(op, filters)]
    cli.table(
        sorted(filtered, key=lambda m: m["fullname"]),
        cols=["fullname", "description"],
        detail=(["main", "flags", "details"] if args.verbose else [])
    )

def _iter_ops(gf_dirs):
    for model in models_impl.iter_models(gf_dirs):
        for op in model.modeldef.operations:
            yield op, model

def _format_op(op, model):
    description, details = util.split_description(op.description)
    return {
        "fullname": "%s:%s" % (model.fullname, op.name),
        "description": description,
        "details": details,
        "model": model.fullname,
        "name": op.name,
        "main": op.main,
        "flags": [
            "%s:%s%s" % (
                flag.name,
                _format_flag_desc(flag),
                _format_flag_value(flag))
            for flag in op.flags
        ]
    }

def _format_flag_desc(flag):
    return " %s" % flag.description if flag.description else ""

def _format_flag_value(flag):
    return " (default is %r)" % flag.default if flag.default is not None else ""

def _filter_op(op, filters):
    filter_vals = [
        op["fullname"],
        op["description"],
    ]
    return util.match_filters(filters, filter_vals)
