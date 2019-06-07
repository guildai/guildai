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
import sys
import warnings

from guild import batch_util
from guild import cli
from guild import config
from guild import index2 as indexlib
from guild import guildfile
from guild import query
from guild import run as runlib
from guild import run_util
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

BASE_COLS = ".run, .operation, .started, .time, .status, .label"
MIN_COLS = ".run"

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
        cli.out("[%s] %s" % (run.short_id, run_util.format_op_desc(run)))
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
    writer = csv.writer(sys.stdout, lineterminator="\n")
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
            index.refresh(runs)
            cols_table = _cols_table(runs, args, index)
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
        runs = [run for run in runs if not batch_util.is_batch(run)]
    return runs

def _cols_table(runs, args, index):
    parse_cache = {}
    return [
        (run, _run_cols(run, args, parse_cache, index))
        for run in runs]

def _run_cols(run, args, parse_cache, index):
    return (
        _core_cols(args, parse_cache),
        _op_cols(run, args, parse_cache, index),
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

def _op_cols(run, args, parse_cache, index):
    if args.skip_op_cols:
        return []
    compare = _run_op_compare(run, index)
    if not compare:
        return []
    cols = []
    for colspec in compare:
        cols.extend(_colspec_cols(colspec, parse_cache))
    return cols

def _run_op_compare(run, index):
    """Returns compare cols for run.

    If we can get the current compare cols for the run op source
    definition (in the Guild file) we use that, otherwise we use the
    run "compare" attr.
    """
    return util.find_apply([
        _try_guildfile_compare,
        _run_compare_attr,
        _default_run_compare], run, index)

def _try_guildfile_compare(run, _index):
    """Returns the current compare for run op if available."""
    try:
        gf = guildfile.from_run(run)
    except (guildfile.NoModels, TypeError):
        return None
    else:
        return _try_guildfile_op_compare(
            gf, run.opref.model_name,
            run.opref.op_name)

def _try_guildfile_op_compare(gf, model_name, op_name):
    try:
        m = gf.models[model_name]
    except KeyError:
        return None
    else:
        op = m.get_operation(op_name)
        return op.compare if op else None

def _run_compare_attr(run, _index):
    return run.get("compare")

def _default_run_compare(run, index):
    return (
        _run_flag_compares(run) +
        _run_scalar_compares(run, index))

def _run_flag_compares(run):
    flags = run.get("flags") or {}
    return ["=%s" % name for name in sorted(flags)]

def _run_scalar_compares(run, index):
    # Assuming index has been refreshed to include run
    scalars = set()
    for s in index.run_scalars(run):
        tag = str(s["tag"])
        if "/" not in tag:
            scalars.add(tag)
    return _apply_step_col(sorted(scalars))

def _apply_step_col(cols):
    if not cols:
        return cols
    return [_step_col_for_cols(cols)] + cols

def _step_col_for_cols(cols):
    if "loss" in cols:
        return "loss step as step"
    return "%s step as step" % cols[0]

def _user_cols(args, parse_cache):
    if not args.cols:
        return []
    return _colspec_cols(args.cols, parse_cache)

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
        "Operation: %s" % run_util.format_op_desc(run),
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
