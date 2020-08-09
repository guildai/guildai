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

from __future__ import absolute_import
from __future__ import division

from guild import cli
from guild import cmd_impl_support
from guild import flag_util
from guild import model
from guild import util

from . import models_impl


def main(args):
    cmd_impl_support.init_model_path()
    filtered = filtered_ops(args)
    cli.table(
        sorted(filtered, key=_op_sort_key),
        cols=["fullname", "description"],
        detail=(["main", "flags", "details"] if args.verbose else []),
    )


def filtered_ops(args):
    dirs = models_impl.models_iter_dirs(args)
    formatted = [_format_op(op, model) for op, model in _iter_ops(dirs)]
    return [op for op in formatted if _filter_op(op, args)]


def _iter_ops(dirs):
    for model in models_impl.iter_models(dirs, include_anonymous=True):
        for op in model.modeldef.operations:
            yield op, model


def _format_op(op, model):
    description, details = util.split_description(op.description)
    return {
        "fullname": format_op_fullname(op.name, model.fullname),
        "description": description,
        "details": details,
        "model": model.fullname,
        "model_name": model.name,
        "name": op.name,
        "main": op.main,
        "flags": [
            "%s:%s%s" % (flag.name, _format_flag_desc(flag), _format_flag_default(flag))
            for flag in op.flags
        ],
        "_model": model,
    }


def format_op_fullname(op_name, model_fullname):
    if model_fullname:
        if model_fullname.endswith("/"):
            return "%s%s" % (model_fullname, op_name)
        return "%s:%s" % (model_fullname, op_name)
    return op_name


def _format_flag_desc(flag):
    return " %s" % flag.description if flag.description else ""


def _format_flag_default(flag):
    return " (default is %s)" % flag_util.encode_flag_val(flag.default)


def _filter_op(op, args):
    filter_vals = [
        op["fullname"],
        op["description"],
    ]
    return (
        (op["name"][:1] != "_" or args.all)
        and (op["model_name"][:1] != "_" or args.all)
        and util.match_filters(args.filters, filter_vals)
    )


def _op_sort_key(op):
    return (_op_type_key(op), op["model"], op["name"])


def _op_type_key(op):
    if isinstance(op["_model"], model.GuildfileModel):
        return 999
    return 0
