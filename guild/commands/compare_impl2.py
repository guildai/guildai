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
from guild import index2 as indexlib
from guild import query

from . import runs_impl

log = logging.getLogger("guild")

def main(args):
    cols = _cols_for_args(args)
    runs = runs_impl.runs_for_args(args)
    _compare(runs, cols)

def _cols_for_args(args):
    base_cols = (
        ".run",
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
    all_cols = range(len(cols))
    header = _table_header(cols)
    index = _init_index(runs)
    rows = _runs_table_data(runs, cols, index)
    cli.table(header + rows, all_cols)

def _table_header(cols):
    return [{
        i: cols[i].header
        for i in range(len(cols))
    }]

def _init_index(runs):
    index = indexlib.RunIndex()
    index.refresh(runs)
    return index

def _runs_table_data(runs, cols, index):
    return [_run_data(run, cols, index) for run in runs]

def _run_data(run, cols, index):
    return {
        i: _format(_col_data(run, col, index))
        for i, col in enumerate(cols)
    }

def _col_data(run, col, index):
    if isinstance(col, query.Flag):
        return _run_flag(run, col)
    elif isinstance(col, query.Attr):
        return index.run_attr(run, col.name)
    elif isinstance(col, query.Scalar):
        return _run_scalar(run, col)
    else:
        assert False, col

def _run_flag(run, flag_col):
    return "yop"

def _run_scalar(run, scalar_col):
    return "yom"

def _format(val):
    if val is None:
        return ""
    return val
