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

import csv
import itertools
import logging
import os
import sys

import six

from guild import batch_util
from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import index as indexlib
from guild import flag_util
from guild import query
from guild import run as runlib
from guild import run_util
from guild import tabview
from guild import util
from guild import var

from . import runs_impl

log = logging.getLogger("guild")

BASE_COLS = ",".join(
    [
        ".run",
        ".operation",
        ".started",
        ".time",
        ".status",
        ".label",
    ]
)

EXTRA_COLS = ".sourcecode"

MIN_COLS = ".run"

NO_RUNS_CAPTION = "no runs"

NO_TABLE_CLIP_WIDTH = pow(10, 10)


def main(args, ctx):
    _check_args(args, ctx)
    _apply_strict_columns(args)
    if args.print_scalars:
        _print_scalars(args)
    elif args.csv:
        _write_csv(args)
    elif args.table:
        _print_table(args)
    elif args.tool:
        _compare_with_tool(args)
    else:
        _tabview(args)


def _check_args(args, ctx):
    cmd_impl_support.check_incompatible_args(
        [
            ("table", "csv"),
            ("table", "tool"),
            ("csv", "tool"),
        ],
        args,
        ctx,
    )


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
        cli.out("[%s] %s" % (run.short_id, run_util.format_operation(run, nowarn=True)))
        for s in index.run_scalars(run):
            key, step, val = (run_util.run_scalar_key(s), s["last_step"], s["last_val"])
            cli.out("  %s: %f (step %i)" % (key, val, step))


def _write_csv(args):
    data = get_data(args, format_cells=False, skip_header_if_empty=True) or []
    with _open_file(args.csv) as out:
        writer = csv.writer(out, lineterminator="\n")
        for row in data:
            writer.writerow([_csv_row_item(x) for x in row])
    if args.csv != "-":
        cli.out("Wrote %i row(s) to %s" % (len(data) - 1, args.csv), err=True)


def _open_file(path):
    if path == "-":
        return util.StdIOContextManager(sys.stdout)
    util.ensure_dir(os.path.dirname(path))
    try:
        return open(path, "w")
    except (OSError, IOError) as e:
        cli.error("error opening %s: %s" % (path, e))


def _csv_row_item(x):
    if isinstance(x, six.string_types):
        return six.ensure_text(x)
    return x


def get_data(args, format_cells=True, skip_header_if_empty=False):
    index = indexlib.RunIndex()
    cb = _get_data_cb(
        args,
        index,
        format_cells=format_cells,
        skip_header_if_empty=skip_header_if_empty,
    )
    data, logs = cb()
    for record in logs:
        log.handle(record)
    return data


def _print_table(args):
    data = get_data(args, skip_header_if_empty=True)
    if not data:
        return
    cols = data[0]
    col_indexes = list(zip(cols, range(len(cols))))

    def format_row(row):
        return {col_name: row[i] for col_name, i in col_indexes}

    heading = {col_name: col_name for col_name in cols}
    data = [heading] + [format_row(row) for row in data[1:]]
    cli.table(data, cols, max_width_adj=NO_TABLE_CLIP_WIDTH)


def _tabview(args):
    config.set_log_output(True)
    index = indexlib.RunIndex()
    tabview.view_runs(
        _get_data_cb(args, index), _get_run_detail_cb(index), _tabview_actions()
    )


def _get_data_cb(args, index, format_cells=True, skip_header_if_empty=False):
    def f():
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
            if args.limit:
                rows = rows[: args.limit]
            if format_cells:
                _format_cells(rows, header, runs)
            log = log_capture.get_all()
            return [header] + rows, log

    return f


def _runs_for_args(args):
    runs = runs_impl.runs_for_args(args)
    if not args.include_batch:
        runs = [run for run in runs if not batch_util.is_batch(run)]
    return runs


def _cols_table(runs, args, index):
    parse_cache = {}
    return [(run, _run_cols(run, args, parse_cache, index)) for run in runs]


def _run_cols(run, args, parse_cache, index):
    return (
        _core_cols(args, parse_cache),
        _op_cols(run, args, parse_cache, index),
        _user_cols(args, parse_cache),
    )


def _core_cols(args, parse_cache):
    return _colspec_cols(_core_colspec(args), parse_cache)


def _core_colspec(args):
    return _base_colspec(args) + _extra_colspec(args)


def _base_colspec(args):
    if args.skip_core:
        return MIN_COLS
    return BASE_COLS


def _extra_colspec(args):
    if args.extra_cols:
        return "," + EXTRA_COLS
    return ""


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
    compare = _op_compare(run, index, args)
    if not compare:
        return []
    cols = []
    for colspec in compare:
        cols.extend(_colspec_cols(colspec, parse_cache))
    return cols


def _op_compare(run, index, args):
    """Returns compare cols for run.

    If we can get the current compare cols for the run op source
    definition (in the Guild file) we use that, otherwise we use the
    run "compare" attr.
    """
    return util.find_apply(
        [
            lambda: run_util.latest_compare(run),
            lambda: _default_run_compare(run, index, args),
        ]
    )


def _default_run_compare(run, index, args):
    return _flag_compares(run) + _scalar_compares(run, index, args)


def _flag_compares(run):
    flags = run.get("flags") or {}
    return ["=%s" % name for name in sorted(flags)]


def _scalar_compares(run, index, args):
    # Assuming index has been refreshed to include run. Not asserting
    # for performance.
    cols = _scalar_cols(run, index, args)
    if not cols:
        return []
    return [_step_col(cols)] + cols


def _scalar_cols(run, index, args):
    metrics = set()
    for s in index.run_scalars(run):
        tag = str(s["tag"])
        if args.all_scalars or runs_impl.filter_default_scalar(tag):
            metrics.add(tag)
    return sorted(metrics)


def _step_col(cols):
    if "loss" in cols:
        return "loss step as step"
    return "%s step as step" % cols[0]


def _user_cols(args, parse_cache):
    if not args.cols:
        return []
    return _colspec_cols(args.cols, parse_cache)


def _resolve_table_cols(table, index):
    return [_resolve_table_section(run, section, index) for run, section in table]


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
    if args.min_col:
        table = _sort_table(table, args.min_col)
    elif args.max_col:
        table = _sort_table(table, args.max_col, reverse=True)
    return _table_rows(table, header)


class _SortKey(object):
    def __init__(self, val, max=False):
        self.val = val
        self.max = max

    def __lt__(self, other):
        try:
            other_val = other.val
        except AttributeError:
            assert False, other
        else:
            return _key_lt(self.val, other_val, self.max)


def _key_lt(val, other, max):
    if val is None:
        return other is not None and not max
    if other is None:
        return max
    val_type = type(val)
    other_type = type(other)
    if val_type == other_type:
        return val < other
    if val_type in (int, float, bool) and other_type in (int, float, bool):
        return val < other
    return str(val) < str(other)


def _sort_table(table, sort_col, reverse=False):
    def key(row):
        for name, val in itertools.chain(row[0], row[1], row[2]):
            if name == sort_col:
                return _SortKey(val, not reverse)
        return _SortKey(None, not reverse)

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
                row[i] = _format_float(val)
            elif isinstance(val, six.string_types):
                row[i] = six.ensure_text(val)
            elif val is True:
                row[i] = "yes"
            elif val is False:
                row[i] = "no"
            else:
                row[i] = str(val)


def _format_float(f):
    """Formats float for compare.

    Uses `flag_util.format_flag` instead of Python's float formatting
    to avoid rounding - esp values like `0.9999999` which should not
    be represented as `1.000000`.
    """
    return flag_util.format_flag(f, truncate_floats=6)


def _get_run_detail_cb(index):
    def f(data, y, _x):
        run_short_id = data[y][0]
        if run_short_id == NO_RUNS_CAPTION:
            return (
                "\nPress 'r' in the main screen to refresh the list.",
                "There are no matching runs currently",
            )
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
        "Operation: %s" % run_util.format_operation(run),
        "From: %s" % run_util.format_pkg_name(run),
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
            lines.append("  %s" % run_util.run_scalar_key(s))
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
            run_short_id,
        )
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
        view.column_width[op_index] = max(view.column_width[op_index], len(new_op))


def _ensure_marked(op):
    if not op.endswith(" [marked]"):
        op += " [marked]"
    return op


def _strip_marked(op):
    if op.endswith(" [marked]"):
        op = op[:-9]
    return op


def _compare_with_tool(args):
    # If tools becomes a generalized facility, this lookup should go
    # through entry points. For now we hardcode the tools and
    # handlers.
    if args.tool == "hiplot":
        _compare_with_hiplot(args)
    else:
        cli.error(
            "unknown compare tool '%s'\n"
            "Refer to TOOLS in 'guild compare --help' for list of supported tools."
            % args.tool
        )


def _compare_with_hiplot(args):
    from guild.plugins import hiplot

    get_data_cb = lambda: get_data(args, format_cells=False)
    hiplot.compare_runs(get_data_cb)
