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
    index = _init_index(runs, cols)
    header = _table_header(cols)
    rows = _runs_table_data(runs, cols, index)
    data, cols = _merge_cols(header, rows)
    _format_data(data)
    cli.table(data, cols)

def _table_header(cols):
    return {
        i: cols[i].header
        for i in range(len(cols))
    }

def _init_index(runs, cols):
    index = indexlib.RunIndex()
    index.refresh(runs, _refresh_types(cols))
    return index

def _refresh_types(cols):
    types = set()
    for col in cols:
        if isinstance(col, query.Flag):
            types.add("flag")
        elif isinstance(col, query.Attr):
            types.add("attr")
        elif isinstance(col, query.Scalar):
            types.add("scalar")
    if not types:
        return None
    return types

def _runs_table_data(runs, cols, index):
    return [_run_data(run, cols, index) for run in runs]

def _run_data(run, cols, index):
    return {
        i: _col_data(run, col, index)
        for i, col in enumerate(cols)
    }

def _col_data(run, col, index):
    if isinstance(col, query.Flag):
        return index.run_flag(run, col.name)
    elif isinstance(col, query.Attr):
        return index.run_attr(run, col.name)
    elif isinstance(col, query.Scalar):
        return index.run_scalar(run, col.key, col.qualifier, col.step)
    else:
        assert False, col

def _merge_cols(header, rows):
    """Merges header and row cols according to header val.

    For columns with the same header, row values are merged so that
    the first non-None col value is moved to the first col occurence
    with that header. Duplicate cols are then dropped.
    """
    header_map = _header_map(header)
    _merge_rows(rows, header_map)
    return [header] + rows, _merged_header_cols(header_map)

def _header_map(header):
    """Returns a map of header name to header index list.

    More than one index will occur if the same header is used more
    than once.
    """
    header_map = {}
    for index, name in sorted(header.items()):
        header_map.setdefault(name, []).append(index)
    return header_map

def _merge_rows(rows, header_map):
    for row in rows:
        for cols in header_map.values():
            # find next non-None value from left to right and apply it
            # to first col
            col0 = cols[0]
            if row[col0] is not None:
                continue
            for next_col in cols[1:]:
                if row[next_col] is not None:
                    row[col0] = row[next_col]
                    break

def _merged_header_cols(header_map):
    """Returns a list of col indexes for merged headers.

    The merged header list is a unique list of header columns with
    repeated header dropped.
    """
    return sorted([cols[0] for cols in header_map.values()])

def _format_data(data):
    for row in data:
        for key, val in row.items():
            if val is None:
                row[key] = ""
