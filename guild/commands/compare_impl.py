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

import csv
import logging
import os
import sys

from guild import cli
from guild import config
from guild import index2 as indexlib
from guild import guildfile
from guild import op_util
from guild import opref as opreflib
from guild import query
from guild import run as runlib
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

BASE_COLS = ".run, .operation, .started, .time, .status, .label"
MIN_COLS = ".run"

def main(args):
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
    data, logs = _get_data_cb(args, index, format_cells)()
    for record in logs:
        log.handle(record)
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
            cols_table = _cols_table(runs, args)
            index.refresh(runs, _refresh_types(cols_table))
            table = _resolve_table_cols(cols_table, index)
            header = _table_header(table)
            rows = _table_rows(table, header)
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

def _cols_table(runs, args):
    parse_cache = {}
    return [(run, _run_cols(run, args, parse_cache)) for run in runs]

def _run_cols(run, args, parse_cache):
    return (
        _core_cols(args, parse_cache),
        _op_cols(run, args, parse_cache),
        _user_cols(args, parse_cache)
    )

def _core_cols(args, parse_cache):
    return _colspec_cols(_core_colspec(args), parse_cache)

def _core_colspec(args):
    if args.skip_core:
        return MIN_COLS
    else:
        return BASE_COLS

def _colspec_cols(colspec, parse_cache):
    try:
        return parse_cache[colspec]
    except KeyError:
        try:
            cols = query.parse("select %s" % colspec).cols
        except query.ParseError as e:
            log.warning("error parsing %r: %s", colspec, e)
            cols = []
        parse_cache[colspec] = cols
        return cols

def _op_cols(run, args, parse_cache):
    if args.skip_op_cols:
        return []
    compare = _run_op_compare(run)
    if not compare:
        return []
    cols = []
    for colspec in compare:
        cols.extend(_colspec_cols(colspec, parse_cache))
    return cols

def _run_op_compare(run):
    """Returns compare cols for run.

    If we can get the current compare cols for the run op source
    definition (in the Guild file) we use that, otherwise we use the
    run "compare" attr.
    """
    compare = _try_guildfile_compare(run)
    if compare is not None:
        return compare
    return run.get("compare", [])

def _try_guildfile_compare(run):
    """Returns the current compare for run op if available."""
    if run.opref.pkg_type != "guildfile":
        return None
    gf_path = run.opref.pkg_name
    if not os.path.exists(gf_path):
        return None
    try:
        gf = guildfile.from_dir(gf_path)
    except guildfile.NoModels:
        return None
    else:
        return _try_guildfile_op_compare(
            gf, run.opref.model_name, run.opref.op_name)

def _try_guildfile_op_compare(gf, model_name, op_name):
    try:
        m = gf.models[model_name]
    except KeyError:
        return None
    else:
        op = m.get_operation(op_name)
        return op.compare if op else None

def _user_cols(args, parse_cache):
    if not args.columns:
        return []
    return _colspec_cols(args.columns, parse_cache)

def _refresh_types(cols_table):
    """Returns a set of types to refresh for cols.

    This scheme is used to avoid refreshing types that aren't needed
    (e.g. scalars are expensive to refresh).
    """
    types = set()
    for _run, sections in cols_table:
        for section in sections:
            for col in section:
                if isinstance(col, query.Flag):
                    types.add("flag")
                elif isinstance(col, query.Attr):
                    types.add("attr")
                elif isinstance(col, query.Scalar):
                    types.add("scalar")
    return types

def _resolve_table_cols(table, index):
    return [
        _resolve_table_section(run, section, index)
        for run, section in table
    ]

def _resolve_table_section(run, section, index):
    return tuple([_resolve_run_cols(run, cols, index) for cols in section])

def _resolve_run_cols(run, cols, index):
    return [(col.header, _col_data(run, col, index)) for col in cols]

def _col_data(run, col, index):
    if isinstance(col, query.Flag):
        val = index.run_flag(run, col.name)
        return op_util.format_flag_val(val)
    elif isinstance(col, query.Attr):
        return index.run_attr(run, col.name)
    elif isinstance(col, query.Scalar):
        prefix, tag = col.split_key()
        return index.run_scalar(run, prefix, tag, col.qualifier, col.step)
    else:
        assert False, col

def _table_header(table):
    header = []
    # Build up headers from oldest run (bottom of table) first to
    # ensure consistency in col ordering as new runs appear.
    reversed_table = reversed(table)
    for section in zip(*reversed_table):
        for row in section:
            for name, _val in row:
                if name not in header:
                    header.append(name)
    return header

def _table_rows(table, header):
    return [_table_row(row, header) for row in table]

def _table_row(row, header):
    return [_row_val(col_name, row) for col_name in header]

def _row_val(col_name, sections):
    val = None
    for cells in sections:
        for cell_name, cell_val in reversed(cells):
            if cell_name == col_name and cell_val is not None:
                val = cell_val
    return val

def _format_cells(rows):
    for row in rows:
        for i, val in enumerate(row):
            if val is None:
                row[i] = ""
            elif isinstance(val, float):
                row[i] = "%0.6f" % val
            else:
                row[i] = str(val)

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
            lines.append("  {}: {}".format(name, val))
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
