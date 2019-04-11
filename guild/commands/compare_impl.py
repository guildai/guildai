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
import itertools
import logging
import os
import sys
import warnings

from guild import cli
from guild import config
from guild import index2 as indexlib
from guild import guildfile
from guild import op_util
from guild import query
from guild import run as runlib
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

BASE_COLS = ".run, .operation, .started, .time, .status, .label"
MIN_COLS = ".run"
DEFAULT_COMPARE = [
    "loss step as step",
    "loss",
    "acc",
]

NO_RUNS_CAPTION = "no runs"

def main(args):
    _apply_strict_columns(args)
    if args.print_scalars:
        _print_scalars(args)
    elif args.format == "csv":
        _print_csv(args)
    elif args.format == "table":
        _print_table(args)
    else:
        _tabview(args)

def _apply_strict_columns(args):
    if args.strict_cols:
        if args.cols:
            cli.error("--cols cannot be used with --strict-cols")
        args.cols = args.strict_cols
        args.skip_core = True
        args.skip_op_cols = True

def _print_scalars(args):
    runs = runs_impl.runs_for_args(args)
    index = indexlib.RunIndex()
    index.refresh(runs, ["scalar"])
    for run in runs:
        cli.out("[%s] %s" % (run.short_id, op_util.format_op_desc(run)))
        for s in index.run_scalars(run):
            prefix = s["prefix"]
            if prefix:
                cli.out("  %s#%s" % (s["prefix"], s["tag"]))
            else:
                cli.out("  %s" % s["tag"])

def _print_csv(args):
    data = _get_data(args, format_cells=False, skip_header_if_empty=True)
    if not data:
        return
    writer = csv.writer(sys.stdout)
    for row in data:
        writer.writerow(row)

def _get_data(args, format_cells=True, skip_header_if_empty=False):
    index = indexlib.RunIndex()
    cb = _get_data_cb(
        args,
        index,
        format_cells=format_cells,
        skip_header_if_empty=skip_header_if_empty)
    data, logs = cb()
    for record in logs:
        log.handle(record)
    return data

def _print_table(args):
    data = _get_data(args, skip_header_if_empty=True)
    if not data:
        return
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
        _get_run_detail_cb(index),
        _tabview_actions())

def _get_data_cb(args, index, format_cells=True, skip_header_if_empty=False):
    def f():
        _try_init_tf_logging()
        log_capture = util.LogCapture()
        with log_capture:
            runs = _runs_for_args(args)
            cols_table = _cols_table(runs, args)
            index.refresh(runs, _refresh_types(cols_table))
            table = _resolve_table_cols(cols_table, index)
            header = _table_header(table)
            if not header:
                if skip_header_if_empty:
                    return [], []
                header = [NO_RUNS_CAPTION]
            rows = _sorted_table_rows(table, header, args)
            if args.top:
                rows = rows[:args.top]
            if format_cells:
                _format_cells(rows, header, runs)
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            import tensorflow as _
        except ImportError:
            pass

def _runs_for_args(args):
    runs = runs_impl.runs_for_args(args)
    if not args.include_batch:
        runs = [run for run in runs if not _is_batch(run)]
    return runs

def _is_batch(run):
    return os.path.exists(run.guild_path("proto"))

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
            cols = query.parse_colspec(colspec).cols
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
    return run.get("compare", DEFAULT_COMPARE)

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
    if not args.cols:
        return []
    return _colspec_cols(args.cols, parse_cache)

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
        return index.run_flag(run, col.name)
    elif isinstance(col, query.Attr):
        return index.run_attr(run, col.name)
    elif isinstance(col, query.Scalar):
        prefix, tag = col.split_key()
        return index.run_scalar(run, prefix, tag, col.qualifier, col.step)
    else:
        assert False, col

def _table_header(table):
    header = []
    for section in zip(*table):
        for row in section:
            for name, _val in row:
                if name not in header:
                    header.append(name)
    return header

def _sorted_table_rows(table, header, args):
    if args.min:
        table = _sort_table(table, args.min)
    elif args.max:
        table = _sort_table(table, args.max, reverse=True)
    return _table_rows(table, header)

def _sort_table(table, sort_col, reverse=False):
    def key(row):
        for name, val in itertools.chain(row[0], row[1], row[2]):
            if name == sort_col:
                return val
        if reverse:
            return float("-inf")
        else:
            return float("inf")
    return sorted(table, key=key, reverse=reverse)

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

def _format_cells(rows, col_names, runs):
    runs_lookup = {run.short_id: run for run in runs}
    for row in rows:
        for i, (name, val) in enumerate(zip(col_names, row)):
            if name == "operation":
                run_id = row[0]
                run = runs_lookup[run_id]
                if run.get("marked"):
                    row[i] += " [marked]"
            elif val is None:
                row[i] = ""
            elif isinstance(val, float):
                row[i] = "%0.6f" % val
            else:
                row[i] = str(val)

def _get_run_detail_cb(index):
    def f(data, y, _x):
        run_short_id = data[y][0]
        if run_short_id == NO_RUNS_CAPTION:
            return (
                "\nPress 'r' in the main screen to refresh the list.",
                "There are no matching runs currently")
        title = "Run {}".format(run_short_id)
        try:
            run_id, path = next(var.find_runs(run_short_id))
        except StopIteration:
            return "This run no longer exists.", title
        else:
            run = runlib.Run(run_id, path)
            index.refresh([run], ["scalar"])
            detail = _format_run_detail(run, index)
            return detail, title
    return f

def _format_run_detail(run, index):
    lines = [
        "Id: %s" % run.id,
        "Operation: %s" % op_util.format_op_desc(run),
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

def _tabview_actions():
    return [
        (("m", "Mark run"), _mark),
        (("u", "Unmark run"), _unmark),
    ]

def _mark(view):
    _mark_impl(view, True)

def _unmark(view):
    _mark_impl(view, False)

def _mark_impl(view, flag):
    if not view.data:
        return
    run_short_id = view.data[view.y][0]
    try:
        run_id, path = next(var.find_runs(run_short_id))
    except StopIteration:
        view.text_box(
            "This run no longer exists.\n"
            "\n"
            "Press 'q' to exist this screen and then press 'r' to "
            "refresh the list.",
            run_short_id)
    else:
        run = runlib.Run(run_id, path)
        _mark_run(run, flag)
        _try_mark_operation(view, flag)

def _mark_run(run, flag):
    if flag:
        run.write_attr("marked", True)
    else:
        run.del_attr("marked")

def _try_mark_operation(view, flag):
    try:
        op_index = view.header.index("operation")
    except ValueError:
        pass
    else:
        op = view.data[view.y][op_index]
        if flag:
            new_op = _ensure_marked(op)
        else:
            new_op = _strip_marked(op)
        view.data[view.y][op_index] = new_op
        view.column_width[op_index] = max(
            view.column_width[op_index],
            len(new_op))

def _ensure_marked(op):
    if not op.endswith(" [marked]"):
        op += " [marked]"
    return op

def _strip_marked(op):
    if op.endswith(" [marked]"):
        op = op[:-9]
    return op
