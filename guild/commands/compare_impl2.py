# Copyright 2017-2019 TensorHub, Inc.
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

import logging

from guild import cli
from guild import query

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    cols = _cols_for_args(args)
    runs = runs_impl.runs_for_args(args)
    _compare(runs, cols)

def _cols_for_args(args):
    base_cols = (
        ".id as run",
        ".model",
        ".operation",
        ".started",
        ".time",
        ".status",
    )
    select_stmt = "select %s, %s" % (",".join(base_cols), args.columns)
    try:
        select = query.parse(select_stmt)
    except query.ParseError as e:
        cli.error(e)
    else:
        return select.cols

def _compare(runs, cols):
    table_cols = range(len(cols))
    header = [{
        i: cols[i].header
        for i in table_cols
    }]
    table_data = header + []
    cli.table(table_data, table_cols)
