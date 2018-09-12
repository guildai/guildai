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

import os

from guild import cli
from guild import resource
from guild import cmd_impl_support
from guild import util

def main(args):
    cmd_impl_support.init_resource_path()
    dirs, filters = cmd_impl_support.guildfile_dirs(args.filters)
    formatted = [_format_resource(r) for r in iter_resources(dirs)]
    filtered = [r for r in formatted if _filter_resource(r, filters)]
    cli.table(
        sorted(filtered, key=lambda r: r["name"]),
        cols=["name", "description"],
        detail=(["sources"] if args.verbose else [])
    )

def iter_resources(dirs):
    abs_dirs = [os.path.abspath(d) for d in dirs]
    for r in resource.iter_resources():
        if not abs_dirs:
            yield r
        try:
            gf = r.dist.guildfile
        except AttributeError:
            pass
        else:
            if any((os.path.abspath(gf.dir) == abs_dir
                    for abs_dir in abs_dirs)):
                yield r

def _format_resource(res):
    return {
        "name": res.fullname,
        "description": res.resdef.description or "",
        "sources": [str(s) for s in res.resdef.sources],
    }

def _filter_resource(res, filters):
    filter_vals = [
        res["name"],
        res["description"],
    ]
    return util.match_filters(filters, filter_vals)
