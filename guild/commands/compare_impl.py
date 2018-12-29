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

import csv
import sys

from guild import cli
from guild import config
from guild import index2 as indexlib
from guild import opref as opreflib
from guild import query
from guild import run as runlib
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

def main(args):
    if args.columns and args.strict_columns:
        cli.error("--columns and --strict-columns cannot both be used")
    if args.print_scalars:
        _print_scalars(args)
    elif args.format == "csv":
        _print_csv(args)
    elif args.format == "table":
        _print_table(args)
    else:
        _tabview(args)

def _print_scalars(args):
    runs = runs_impl.runs_for_args(args)
    index = indexlib.RunIndex()
    index.refresh(runs, ["scalar"])
    for run in runs:
        opref = opreflib.OpRef.from_run(run)
        cli.out("[%s] %s" % (run.short_id, runs_impl.format_op_desc(opref)))
        for s in index.run_scalars(run):
            prefix = s["prefix"]
            if prefix:
                cli.out("  %s#%s" % (s["prefix"], s["tag"]))
            else:
                cli.out("  %s" % s["tag"])

def _print_csv(args):
    data = _get_data(args, format_cells=False)
    writer = csv.writer(sys.stdout)
    for row in data:
        writer.writerow(row)

def _get_data(args, format_cells=True):
    index = indexlib.RunIndex()
    data, _logs = _get_data_cb(args, index, format_cells)()
    return data

def _print_table(args):
    data = _get_data(args)
    cols = data[0]
    col_indexes = list(zip(cols, range(len(cols))))
    def format_row(row):
        return {
            col_name: row[i]
            for col_name, i in col_indexes
        }
    heading = {
        col_name: col_name
        for col_name in cols
    }
    data = [heading] + [format_row(row) for row in data[1:]]
    cli.table(data, cols)

def _tabview(args):
    config.set_log_output(True)
    index = indexlib.RunIndex()
    tabview.view_runs(
        _get_data_cb(args, index),
        _get_run_detail_cb(index))

def _get_data_cb(args, index, format_cells=True):
    def f():
        _try_init_tf_logging()
        log_capture = util.LogCapture()
        with log_capture:
            runs = runs_impl.runs_for_args(args)
            cols = _init_cols(args, runs)
            refresh_types = _refresh_types(cols)
            index.refresh(runs, refresh_types)
            header = _table_header(cols)
            rows = _runs_table_data(runs, cols, index)
            header, rows = _merge_cols(header, rows)
            if format_cells:
                _format_cells(rows)
            log = log_capture.get_all()
        return [header] + rows, log
    return f

def _try_init_tf_logging():
    """Load TensorFlow, forcing init of TF logging.

    This is part of our handing of logging, which can interfere with
    the curses display used by tabview. By forcing an init of TF logs,
    we can patch loggers with LogCapture (see guild.tabview module)
    for display in a curses window.
    """
    try:
        import tensorflow as _
    except ImportError:
        pass

def _init_cols(args, runs):
    select_stmt = _init_select_stmt(args, runs)
    try:
        select = query.parse(select_stmt)
    except query.ParseError as e:
        cli.error(e)
    else:
        return select.cols

def _init_select_stmt(args, runs):
    assert not (args.columns and args.strict_columns)
    if args.strict_columns:
        base_cols = (".run",)
    else:
        base_cols = (
            ".run",
            ".model",
            ".operation",
            ".started",
            ".time",
            ".status",
        )
    stmt = "select %s" % ",".join(base_cols)
    if not args.strict_columns:
        runs_cols = _runs_compare_cols(runs)
        if runs_cols:
            stmt += ", %s" % ",".join(runs_cols)
    if args.columns:
        stmt += ", %s" % args.columns
    if args.strict_columns:
        stmt += ", %s" % args.strict_columns
    return stmt

def _runs_compare_cols(runs):
    cols = []
    for run in runs:
        for col in run.get("compare", []):
            if col not in cols:
                cols.append(col)
    return cols

def _refresh_types(cols):
    """Returns a set of types to refresh for cols.

    This scheme is used to avoid refreshing types that aren't needed
    (e.g. scalars are expensive to refresh).
    """
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

def _table_header(cols):
    return [col.header for col in cols]

def _runs_table_data(runs, cols, index):
    return [_run_data(run, cols, index) for run in runs]

def _run_data(run, cols, index):
    return [_col_data(run, col, index) for col in cols]

def _col_data(run, col, index):
    if isinstance(col, query.Flag):
        return index.run_flag(run, col.name)
    elif isinstance(col, query.Attr):
        return index.run_attr(run, col.name)
    elif isinstance(col, query.Scalar):
        prefix, tag = col.split_key()
        return index.run_scalar(run, prefix, tag, col.qualifier, col.step)
    else:
        assert False, col

def _merge_cols(header, rows):
    """Merges header and row cols according to header val.

    For columns with the same header, row values are merged so that
    the first non-None col value is moved to the first col occurence
    with that header. Duplicate cols are then dropped.
    """
    header_map = _header_map(header)
    return (
        _merge_header(header_map),
        _merge_row_cells(rows, header_map)
    )

def _header_map(header):
    """Returns a map of header name to header index list.

    More than one index will occur if the same header is used more
    than once.
    """
    header_map = {}
    for i, name in enumerate(header):
        header_map.setdefault(name, []).append(i)
    return header_map

def _merge_header(header_map):
    """Returns a new header list from a header map.

    header_map is a map of header names to column indices. Uses the
    first column index to position the header name in the merged list.
    """
    sorted_cols = sorted([(cols, name) for name, cols in header_map.items()])
    return [name for _, name in sorted_cols]

def _merge_row_cells(rows, header_map):
    """Returns a new list of rows with merged cells.
    """
    col_indices = sorted(header_map.values())
    return [_merge_row(row, col_indices) for row in rows]

def _merge_row(row, col_indices):
    """Returns a new row with merged cells.

    col_indices must be a list of col indices sorted in ascending
    order. Each list of indices is used to find and apply from left to
    right non-None values to the row cell corresponding to the list
    position in cols.
    """
    merged = [None] * len(col_indices)
    for i, cols in enumerate(col_indices):
        for col in cols:
            if row[col] is not None:
                merged[i] = row[col]
                break
    return merged

def _format_cells(rows):
    for row in rows:
        for i, val in enumerate(row):
            if val is None:
                row[i] = ""
            elif isinstance(val, float):
                row[i] = "%0.6f" % val

def _get_run_detail_cb(index):
    def f(data, y, _x):
        run_short_id = data[y][0]
        title = "Run {}".format(run_short_id)
        try:
            run_id, path = next(var.find_runs(run_short_id))
        except StopIteration:
            return "This run no longer exists", title
        else:
            run = runlib.Run(run_id, path)
            index.refresh([run], ["scalar"])
            detail = _format_run_detail(run, index)
            return detail, title
    return f

def _format_run_detail(run, index):
    opref = opreflib.OpRef.from_run(run)
    lines = [
        "Id: %s" % run.id,
        "Model: %s" % opref.model_name,
        "Operation: %s" % opref.op_name,
        "Status: %s" % run.status,
        "Started: %s" % util.format_timestamp(run.get("started")),
        "Stopped: %s" % util.format_timestamp(run.get("stopped")),
        "Label: %s" % (run.get("label") or ""),
    ]
    flags = run.get("flags")
    if flags:
        lines.append("Flags:")
        for name, val in sorted(flags.items()):
            val = val if val is not None else ""
            lines.append("  {}: {}".format(name.decode(), val))
    scalars = list(index.run_scalars(run))
    if scalars:
        lines.append("Scalars:")
        for s in scalars:
            prefix = s["prefix"]
            if prefix:
                lines.append("  %s#%s" % (s["prefix"], s["tag"]))
            else:
                lines.append("  %s" % s["tag"])
    return "\n".join(lines)
