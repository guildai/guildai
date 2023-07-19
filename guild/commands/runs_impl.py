# Copyright 2017-2023 Posit Software, PBC
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

import datetime
import inspect
import io
import json
import logging
import os
import re
import typing
import uuid

# IMPORTANT: Keep expensive imports out of this list. This module is
# used by several commands and any latency here will be automatically
# applied to those commands. If the import is used once or twice, move
# it into the applicable function(s). If it's used more than once or
# twice, move the command impl into a separate module (see
# publish_impl for example).

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import exit_code
from guild import filter_util
from guild import flag_util
from guild import op_util
from guild import remote_run_support
from guild import run as runlib
from guild import run_util
from guild import util
from guild import var
from guild import yaml_util

from . import remote_impl_support

log = logging.getLogger("guild")

RUN_DETAIL = [
    "id",
    "operation",
    "from",
    "status",
    "started",
    "stopped",
    "marked",
    "label",
    "sourcecode_digest",
    "vcs_commit",
    "run_dir",
    "command",
    "exit_status",
    "pid",
]

ALL_RUNS_ARG = [":"]
LATEST_RUN_ARG = ["1"]

RUNS_PER_GROUP = 20

STATUS_FILTERS = [
    ("completed", "status_completed"),
    ("error", "status_error"),
    ("pending", "status_pending"),
    ("running", "status_running"),
    ("staged", "status_staged"),
    ("terminated", "status_terminated"),
]

if not os.getenv("SHELL"):
    # Windows command prompt wants a space buffer to avoid wrapping.
    STYLE_TABLE_WIDTH_ADJ = -1
else:
    STYLE_TABLE_WIDTH_ADJ = 0


def runs_for_args(args, ctx=None):
    filtered = filtered_runs(args, ctx)
    return select_runs(filtered, args.runs, ctx)


def filtered_runs(args, ctx=None):
    if getattr(args, "remote", None):
        return remote_impl_support.filtered_runs(args)
    try:
        return filter_util.filtered_runs(
            args.filter_expr,
            root=_runs_root_for_args(args),
            sort=["-timestamp"],
            base_filter=_runs_filter(args, ctx),
        )
    except SyntaxError as e:
        _filter_syntax_error(e)


def _filter_syntax_error(e) -> typing.NoReturn:
    e = str(e)
    m = re.search(r"line (\d+), pos (\d+): (.*)", e)
    if not m:
        if e == "Syntax error at EOF":
            cli.error("syntax error in filter - unexpected end of expresion")
        else:
            cli.error(f"invalid filter expression: {e}")
    elif m.group(1) == "1":
        cli.error(f"syntax error in filter at position {m.group(2)}: {m.group(3)}")
    else:
        cli.error(
            f"syntax error in filter on line {m.group(1)}, "
            f"position {m.group(2)}: {m.group(3)}"
        )


def _runs_root_for_args(args):
    archive = getattr(args, "archive", None)
    deleted = getattr(args, "deleted", False)
    if archive and deleted:
        cli.error("--archive and --deleted cannot both be used")
    if archive:
        return _validated_archive_path(archive)
    return var.runs_dir(deleted=deleted)


def _validated_archive_path(archive_arg):
    if os.path.exists(archive_arg):
        return archive_arg
    archive = _archive_for_name(archive_arg)
    if archive:
        return archive.path
    cli.error(
        f"'{archive_arg}' is not a valid archive - use a path to a "
        "file/directory or specify an archive name returned by "
        "'guild archive --list'."
    )


def _runs_filter(args, ctx):
    filters = []
    _apply_status_filter(args, filters)
    _apply_ops_filter(args, filters)
    _apply_labels_filter(args, filters)
    _apply_tags_filter(args, filters)
    _apply_comments_filter(args, filters)
    _apply_marked_filter(args, filters)
    _apply_started_filter(args, ctx, filters)
    _apply_sourcecode_digest_filter(args, filters)
    return var.run_filter("all", filters)


def _apply_status_filter(args, filters):
    true_status, false_status = _status_filter_args(args)
    if true_status:
        filters.append(
            var.run_filter(
                "any",
                [var.run_filter("attr", "status", status) for status in true_status],
            )
        )
    if false_status:
        filters.append(
            var.run_filter(
                "all",
                [var.run_filter("!attr", "status", status) for status in false_status],
            )
        )


def _status_filter_args(args):
    status_args = [
        (status, getattr(args, arg_name, None)) for status, arg_name in STATUS_FILTERS
    ]
    return (
        [status for status, val in status_args if val is True],
        [status for status, val in status_args if val is False],
    )


def _apply_ops_filter(args, filters):
    if args.filter_ops:
        filters.append(operation_filter(args.filter_ops))


def operation_filter(op_refs):
    def f(run):
        opspec = run_util.format_operation(run, nowarn=True)
        return any((_compare_op(ref, opspec) for ref in op_refs))

    return f


def _compare_op(ref, opspec):
    if ref.startswith("^") or ref.endswith("$"):
        return _re_match(ref, opspec)
    return _opspec_match(ref, opspec)


def _re_match(pattern, target):
    try:
        return re.search(pattern, target)
    except re.error:
        return False


def _opspec_match(ref, opspec):
    ref_parts = _split_opspec(ref)
    opspec_parts = _split_opspec(opspec)
    assert len(ref_parts) == 3 and len(opspec_parts) == 3, (ref_parts, opspec_parts)
    for ref_part, opspec_part in zip(ref_parts, opspec_parts):
        if not _opspec_part_match(ref_part, opspec_part):
            return False
    return True


def _split_opspec(opspec):
    parsed = op_util.parse_opspec(opspec)
    if parsed:
        model, op = parsed
        pkg, model = _split_model_pkg(model)
        return pkg, model, op
    return None, None, None


def _split_model_pkg(model):
    if model:
        parts = model.split("/", 1)
        if len(parts) == 2:
            return parts
    return None, model


def _opspec_part_match(ref, part):
    if not ref:
        return True
    if not part:
        return False
    if "*" in ref:
        return _opspec_part_fnmatch(ref, part)
    return ref == part


def _opspec_part_fnmatch(ref, part):
    from fnmatch import fnmatch

    return fnmatch(part, ref)


def _apply_labels_filter(args, filters):
    if args.filter_labels and args.filter_unlabeled:
        cli.error("--label and --unlabeled cannot both be used")
    if args.filter_labels:
        filters.append(_labels_filter(args.filter_labels))
    elif args.filter_unlabeled:
        filters.append(_unlabeled_filter())


def _labels_filter(filter_vals):
    def f(run):
        run_label = str(run.get("label", "")).strip()
        return any((_match_label(s, run_label) for s in filter_vals))

    return f


def _match_label(s, run_label):
    if s == "-":
        return not run_label
    return s in run_label


def _unlabeled_filter():
    def f(run):
        return not run.get("label", "").strip()

    return f


def _apply_tags_filter(args, filters):
    if args.filter_tags:
        filters.append(_tags_filter(args.filter_tags))


def _tags_filter(tags):
    def f(run):
        run_tags = run.get("tags") or []
        return any((t in run_tags for t in tags))

    return f


def _apply_comments_filter(args, filters):
    if args.filter_comments:
        filters.append(_comments_filter(args.filter_comments))


def _comments_filter(filter_vals):
    def f(run):
        comment_text = _run_comments_text(run)
        return any((_match_comments(s, comment_text) for s in filter_vals))

    return f


def _run_comments_text(run):
    comments = run.get("comments") or []
    return "\n".join([_run_comment_filter_text(comment) for comment in comments])


def _run_comment_filter_text(comment):
    return "\n".join(
        [
            (comment.get("user") or "").lower(),
            (comment.get("host") or "").lower(),
            (comment.get("body") or "").lower(),
        ]
    )


def _match_comments(s, comment_text):
    if s == "-":
        return not comment_text
    return s.lower() in comment_text


def _apply_marked_filter(args, filters):
    if args.filter_marked and args.filter_unmarked:
        cli.error("--marked and --unmarked cannot both be used")
    if args.filter_marked:
        filters.append(_marked_filter())
    if args.filter_unmarked:
        filters.append(_marked_filter(False))


def _marked_filter(test_for=True):
    def f(run):
        marked = bool(run.get("marked"))
        return marked if test_for is True else not marked

    return f


def _apply_started_filter(args, ctx, filters):
    if args.filter_started:
        start, end = _parse_timerange(args.filter_started, ctx)
        log.debug("time range filter: %s to %s", start, end)
        filters.append(started_filter(start, end))


def _parse_timerange(spec, ctx):
    from guild import timerange

    try:
        return timerange.parse_spec(spec)
    except ValueError as e:
        cli.error(f"invalid RANGE: {e}{_range_help_suffix(ctx)}")


def _apply_sourcecode_digest_filter(args, filters):
    if args.filter_digest:
        filters.append(_digest_filter(args.filter_digest))


def _digest_filter(prefix):
    def f(run):
        return run.get("sourcecode_digest", "").startswith(prefix)

    return f


def _range_help_suffix(ctx):
    if not ctx:
        return ""
    return f"\nTry '{ctx.command_path} --help' for help specifying time ranges."


def started_filter(start, end):
    def f(run):
        started = run.timestamp
        if not started:
            log.debug("%s no timestamp, skipping", run.id)
            return False
        started = datetime.datetime.fromtimestamp(started // 1000000)
        if start and started < start:
            log.debug("%s timestamp %s < %s, skipping", run.id, started, start)
            return False
        if end and started >= end:
            log.debug("%s timestamp %s >= %s, skipping", run.id, started, start)
            return False
        log.debug("%s timestamp %s in range", run.id, started)
        return True

    return f


def select_runs(runs, select_specs, ctx=None):
    if not select_specs:
        return runs
    selected = []
    for spec in select_specs:
        try:
            slice_start, slice_end = _parse_slice(spec)
        except ValueError:
            selected.append(_find_run_by_id(spec, runs, ctx))
        else:
            if _in_range(slice_start, slice_end, runs):
                selected.extend(runs[slice_start:slice_end])
            else:
                selected.append(_find_run_by_id(spec, runs, ctx))
    return selected


def _parse_slice(spec):
    try:
        index = int(spec)
    except ValueError as e:
        m = re.match("(\\d+)?:(\\d+)?", spec)
        if m:
            try:
                return (_slice_part(m.group(1), decr=True), _slice_part(m.group(2)))
            except ValueError:
                pass
        raise ValueError(spec) from e
    else:
        return index - 1, index


def _slice_part(s, decr=False):
    if s is None:
        return None
    if decr:
        return int(s) - 1
    return int(s)


def _find_run_by_id(id_part, runs, ctx):
    matches = [run for run in runs if run.id.startswith(id_part)]
    return cmd_impl_support.one_run(matches, id_part, ctx)


def _in_range(slice_start, slice_end, l):
    return (
        (slice_start is None or slice_start >= 0)
        and (slice_end is None or slice_end <= len(l))
    )


def list_runs(args, ctx=None):
    if args.remote:
        remote_impl_support.list_runs(args)
    else:
        _list_runs(args, ctx)


def _list_runs(args, ctx):
    _check_list_runs_args(args, ctx)
    runs = filtered_runs(args, ctx=ctx)
    if args.comments:
        _list_runs_comments(_limit_runs(runs, args), args, comment_index_format=False)
    elif args.json:
        if args.limit or args.more or args.all:
            cli.note("--json option always shows all runs")
        _list_runs_json(runs)
    else:
        _list_runs_(_limit_runs(runs, args), args)


def _check_list_runs_args(args, ctx):
    cmd_impl_support.check_incompatible_args(
        [
            ("comments", "verbose"),
            ("comments", "json"),
            ("json", "verbose"),
            ("archive", "deleted"),
            ("all", "limit"),
        ],
        args,
        ctx,
    )


def _list_runs_json(runs):
    runs_data = [_listed_run_json_data(run) for run in runs]
    cli.out(json.dumps(runs_data))


def _listed_run_json_data(run):
    run_data = _run_data(
        run,
        (
            "exit_status",
            "cmd",
            "comments",
            "marked",
            "label",
            "started",
            "status",
            "stopped",
            "tags",
        ),
    )
    _apply_batch_proto(run, run_data)
    return run_data


def _run_data(run, attrs):
    data = {
        "id": run.id,
        "run_dir": run.path,
        "opref": str(run.opref) if run.opref else "",
    }
    data.update({name: _run_attr(run, name) for name in attrs})
    return data


def _run_attr(run, name):
    base_attrs = ("status",)
    if name in base_attrs:
        return getattr(run, name)
    return run.get(name)


def _apply_batch_proto(run, data):
    proto_dir = run.guild_path("proto")
    if os.path.exists(proto_dir):
        proto = runlib.for_dir(proto_dir)
        data["batch_proto"] = _listed_run_json_data(proto)


def _list_runs_(runs, args):
    formatted = format_runs(_limit_runs(runs, args))
    cols = _cols_for_list(args)
    detail = RUN_DETAIL if args.verbose else None
    cli.table(formatted, cols, detail=detail, max_width_adj=STYLE_TABLE_WIDTH_ADJ)


def _cols_for_list(args):
    if args.simplified:
        return [
            "num_index",
            "op_desc",
            "status_with_remote",
            "label",
        ]
    return [
        "index",
        "op_desc",
        "started",
        "status_with_remote",
        "label",
    ]


def _limit_runs(runs, args):
    if args.all:
        return runs
    if args.limit and args.limit > 0:
        return runs[:args.limit]
    limited = runs[:(args.more + 1) * RUNS_PER_GROUP]
    if len(limited) < len(runs):
        cli.note(
            f"Showing the first {len(limited)} runs ({len(runs)} total) - use --all "
            "to show all or -m to show more"
        )
    return limited


def format_runs(runs):
    formatted = []
    for i, run in enumerate(runs):
        try:
            formatted_run = run_util.format_run(run, i + 1)
        except Exception:
            log.exception("formatting run in %s", run.path)
        else:
            formatted.append(formatted_run)
    _apply_op_desc(formatted)
    return formatted


def _apply_op_desc(formatted):
    for fmt_run in formatted:
        op_desc = _op_desc_base(fmt_run)
        marked_suffix = " [marked]" if fmt_run["marked"] == "yes" else ""
        fmt_run["op_desc"] = op_desc + marked_suffix


def _op_desc_base(fmt_run, apply_style=True):
    op = fmt_run["operation"]
    op_dir = run_util.run_op_dir(fmt_run["_run"])
    if not op_dir:
        return _empty_style(op, apply_style)
    op_dir_suffix = _styled_op_dir_suffix(op_dir, apply_style)
    return f"{op}{op_dir_suffix}"


def _empty_style(s, apply_style):
    # Pad a string with an empty style for alignment in tables.
    if apply_style:
        return s + cli.style("", dim=True)
    return s


def _styled_op_dir_suffix(op_dir, apply_style):
    cwd = os.path.abspath(config.cwd())
    if util.compare_paths(op_dir, cwd):
        return _empty_style("", apply_style)
    shortened_op_dir = run_util.shorten_op_dir(op_dir, cwd)
    return _dim_style(f" ({shortened_op_dir})", apply_style)


def _dim_style(s, apply_style):
    if apply_style:
        return cli.style(s, dim=True)
    return s


def format_run(run):
    formatted = format_runs([run])
    if not formatted:
        raise ValueError(f"error formatting {run}")
    assert len(formatted) == 1, formatted
    return formatted[0]


def _no_selected_runs_exit(help_msg=None):
    help_msg = help_msg or (
        "No matching runs\n"
        "Try 'guild runs list' to list available runs."
    )
    cli.out(help_msg, err=True)
    raise SystemExit(0)


def runs_op(
    args,
    ctx,
    preview_msg,
    confirm_prompt,
    no_runs_help,
    op_callback,
    default_runs_arg=None,
    confirm_default=False,
    runs_callback=None,
):
    get_selected = runs_callback or runs_op_selected
    selected = get_selected(args, ctx, default_runs_arg)
    if not selected:
        _no_selected_runs_exit(no_runs_help)
    formatted = None  # expensive, lazily init as needed
    if not args.yes:
        cli.out(preview_msg, err=True)
        formatted = format_runs(selected)
        cols = [
            "short_index",
            "op_desc",
            "started",
            "status_with_remote",
            "label",
        ]
        cli.table(formatted, cols, indent=2, err=True)
        fmt_confirm_prompt = confirm_prompt.format(count=len(selected))
        if not cli.confirm(fmt_confirm_prompt, confirm_default):
            raise SystemExit(exit_code.ABORTED)
    _apply_runs_op_callback(op_callback, selected, formatted)


def _apply_runs_op_callback(op_callback, selected, formatted):
    if len(inspect.signature(op_callback).parameters) == 2:
        if formatted is None:
            formatted = format_runs(selected)
        op_callback(selected, formatted)
    else:
        op_callback(selected)


def runs_op_selected(args, ctx, default_runs_arg=None):
    default_runs_arg = default_runs_arg or ALL_RUNS_ARG
    runs_arg = _remove_duplicates(args.runs or default_runs_arg)
    filtered = filtered_runs(args, ctx)
    return select_runs(filtered, runs_arg, ctx)


def _remove_duplicates(vals):
    deduped = []
    for val in vals:
        if val not in deduped:
            deduped.append(val)
    return deduped


def delete_runs(args, ctx=None):
    if args.remote:
        remote_impl_support.delete_runs(args)
    else:
        _delete_runs(args, ctx)


def _delete_runs(args, ctx):
    if args.permanent:
        preview = cmd_impl_support.format_warn(
            "WARNING: You are about to permanently delete the following runs:"
        )
        confirm = "Permanently delete {count} run(s)?"
    else:
        preview = "You are about to delete the following runs:"
        confirm = "Delete {count} run(s)?"
    no_runs_help = "Nothing to delete."

    def delete(selected):
        stoppable = [
            run for run in selected if run.status == "running" and not run.remote
        ]
        if stoppable and not args.yes:
            cli.out(
                cmd_impl_support.format_warn(
                    "WARNING: One or more runs are still running "
                    "and will be stopped before being deleted."
                ),
                err=True,
            )
            if not cli.confirm("Really delete these runs?"):
                raise SystemExit(exit_code.ABORTED)
        for run in stoppable:
            _stop_run(run, no_wait=True)
        var.delete_runs(selected, args.permanent)
        if args.permanent:
            cli.out(f"Permanently deleted {len(selected)} run(s)", err=True)
        else:
            cli.out(f"Deleted {len(selected)} run(s)", err=True)

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs_help,
        delete,
        confirm_default=not args.permanent,
    )


def purge_runs(args, ctx):
    if args.remote:
        remote_impl_support.purge_runs(args)
    else:
        _purge_runs(args, ctx)


def _purge_runs(args, ctx):
    preview = cmd_impl_support.format_warn(
        "WARNING: You are about to permanently delete the following runs:"
    )
    confirm = "Permanently delete {count} run(s)?"
    no_runs_help = "Nothing to purge."

    def purge(selected):
        var.purge_runs(selected)
        cli.out(f"Permanently deleted {len(selected)} run(s)", err=True)

    runs_op(args.copy(deleted=True), ctx, preview, confirm, no_runs_help, purge)


def restore_runs(args, ctx):
    if args.remote:
        remote_impl_support.restore_runs(args)
    else:
        _restore_runs(args, ctx)


def _restore_runs(args, ctx):
    preview = "You are about to restore the following runs:"
    confirm = "Restore {count} run(s)?"
    no_runs_help = "Nothing to restore."

    def restore(selected):
        var.restore_runs(selected)
        cli.out(f"Restored {len(selected)} run(s)", err=True)

    runs_op(
        args.copy(deleted=True),
        ctx,
        preview,
        confirm,
        no_runs_help,
        restore,
        confirm_default=True,
    )


def run_info(args, ctx):
    if args.remote:
        remote_impl_support.run_info(args)
    else:
        _run_info(args, ctx)


def _run_info(args, ctx):
    run = one_run(args, ctx)
    _print_run_info(run, args)


def one_run(args, ctx):
    filtered = filtered_runs(args, ctx=ctx)
    if not filtered:
        cli.error("no matching runs")
    runspec = args.run or "1"
    selected = select_runs(filtered, [runspec], ctx)
    return cmd_impl_support.one_run(selected, runspec, ctx)


def _print_run_info(run, args):
    data = _run_info_data(run, args)
    if args.json:
        _print_run_info_json(data)
    else:
        _print_run_info_ordered(data)


def _run_info_data(run, args):
    data = []
    _append_run_attr_data(run, args.private_attrs, data)
    data.append(("tags", run.get("tags") or []))
    data.append(("flags", run.get("flags") or {}))
    proto = run.batch_proto
    if proto:
        data.append(("proto-flags", proto.get("flags") or {}))
    data.append(("scalars", _scalar_info(run, args)))
    other_attrs = _opdef_and_logged_attrs(run, args.private_attrs)
    if other_attrs:
        data.append(("attributes", other_attrs))
    if args.comments:
        data.append(("comments", _format_comments_for_run_info(run)))
    if args.env:
        data.append(("environment", run.get("env") or {}))
    if args.manifest:
        data.append(("manifest", _format_run_manifest(run)))
    if args.deps:
        data.append(("dependencies", run.get("deps") or {}))
    if args.plugins:
        data.append(("plugins", run.get("plugins") or []))
    if args.private_attrs and args.json:
        _maybe_append_proto_data(run, data)
    return data


def _format_comments_for_run_info(run):
    return [
        _format_comment_for_run_info(comment)
        for comment in (run.get("comments") or [])
    ]


def _format_comment_for_run_info(comment):
    if not isinstance(comment, dict):
        return repr(comment)
    return {
        "user": comment.get("user") or "",
        "host": comment.get("host") or "",
        "time": util.format_timestamp(comment.get("time")),
        "body": (comment.get("body") or "").strip(),
    }


def _append_run_attr_data(run, include_private, data):
    fmt_run = format_run(run)
    for name in RUN_DETAIL:
        data.append((name, fmt_run[name]))
    if include_private:
        data.append(("opref", str(run.opref)))
        data.append(("op", run.get("op")))


def _opdef_and_logged_attrs(run, include_private):
    return _filter_core_attrs(
        {
            **(run.get("opdef_attrs") or {}),
            **_logged_attrs(run, include_private),
        }
    )


def _logged_attrs(run, include_private):
    from guild import index  # expensive

    return {
        name: val
        for name, val in index.logged_attrs(run).items()
        if include_private or name[:1] != "_"
    }


def _filter_core_attrs(attrs):
    return {name: attrs[name] for name in attrs if name not in runlib.CORE_RUN_ATTRS}


def _scalar_info(run, args):
    try:
        return _scalar_info_(run, args)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("get scalars")
        return cmd_impl_support.format_warn(f"ERROR: {e}")


def _scalar_info_(run, args):
    return {
        key: val
        for key, val in _iter_scalars(run, args)
        if args.all_scalars or filter_default_scalar(key)
    }


def filter_default_scalar(key):
    _prefix, tag = _split_scalar_key(key)
    return not tag.startswith("sys/")


def _split_scalar_key(key):
    parts = key.split("#", 1)
    return ("", parts[0]) if len(parts) == 1 else (parts[0], parts[1])


def _iter_scalars(run, args):
    from guild import index  # expensive

    for s in index.iter_run_scalars(run):
        key = run_util.run_scalar_key(s)
        if args.all_scalars:
            yield key, _scalar_vals(s, args)
        else:
            yield key, _scalar_last_val(s, args)


def _scalar_vals(s, args):
    return {
        "first": _scalar_val(s, "first_val", "first_step", args.json),
        "last": _scalar_val(s, "last_val", "last_step", args.json),
        "min": _scalar_val(s, "min_val", "min_step", args.json),
        "max": _scalar_val(s, "max_val", "min_step", args.json),
        "avg": _scalar_val(s, "avg_val", "count", args.json),
        "total": _scalar_val(s, "total", "count", args.json),
    }


def _scalar_last_val(s, args):
    return _scalar_val(s, "last_val", "last_step", args.json)


def _scalar_val(s, val_key, step_key, format_json):
    val = s[val_key]
    step = s[step_key]
    if format_json:
        return val, step
    return _format_scalar_val(val, step)


def _format_scalar_val(val, step):
    if isinstance(val, float):
        return f"{val:.6f} (step {step})"
    # Defensive here - val should None but we don't assert because
    # this is a summary op.
    val = "nan" if val is None else val
    return f"{val} (step {step})"


def _format_run_manifest(run):
    from guild import run_manifest

    try:
        m = run_manifest.manifest_for_run(run.dir)
    except Exception as e:
        log.error("cannot read run manifest: %s", e)
        return {}
    else:
        return _formatted_run_manifest_items(m)


def _formatted_run_manifest_items(m):
    formatted = {}
    for args in m:
        _apply_formatted_manifest_args(args, formatted)
    return {name: sorted(items) for name, items in formatted.items()}


def _apply_formatted_manifest_args(args, formatted):
    type = args[0]
    if type == "s":
        _apply_formatted_manifest_sourcecode_file(args[1:], formatted)
    elif type == "d":
        _apply_formatted_manifest_dep(args[1:], formatted)


def _apply_formatted_manifest_sourcecode_file(args, formatted):
    section = formatted.setdefault("sourcecode", [])
    section.append(args[0])


def _apply_formatted_manifest_dep(args, formatted):
    section = formatted.setdefault("dependencies", [])
    section.append(args[0])


def _maybe_append_proto_data(run, data):
    proto = run.batch_proto
    if proto:
        proto_data = []
        _append_run_attr_data(proto, True, proto_data)
        data.append(("proto-run", proto_data))


def _print_run_info_json(data):
    data = _tuple_lists_to_dict(data)
    cli.out(json.dumps(data))


def _tuple_lists_to_dict(data):
    if isinstance(data, list):
        if data and isinstance(data[0], tuple):
            return {name: _tuple_lists_to_dict(val) for name, val in data}
        return [_tuple_lists_to_dict(val) for val in data]
    return data


def _print_run_info_ordered(data):
    for name, val in data:
        if isinstance(val, list):
            _print_run_info_list(name, val)
        elif isinstance(val, dict):
            _print_run_info_dict(name, val)
        else:
            cli.out(f"{name}: {val}")


def _print_run_info_list(name, val):
    cli.out(f"{name}:")
    for item in val:
        if isinstance(item, dict):
            cli.out("  -")
            for item_name, item_val in sorted(item.items()):
                encoded = _fix_quoted_string(flag_util.encode_flag_val(item_val))
                if "\n" in encoded:
                    cli.out(_indent(f"{item_name}: |", 4))
                    cli.out(_indent(_unindent(encoded), 6))
                else:
                    cli.out(_indent(f"{item_name}: {encoded}", 4))
        else:
            cli.out(f"  - {flag_util.encode_flag_val(item)}")


def _print_run_info_dict(name, val):
    cli.out(f"{name}:")
    for item_name, item_val in _sort_run_info_attr(name, val):
        if isinstance(item_val, list):
            cli.out(f"  {item_name}:")
            for item_item in item_val:
                cli.out(f"    - {flag_util.encode_flag_val(item_item)}")
        elif isinstance(item_val, dict):
            cli.out(f"  {item_name}:")
            # Use full YAML formatting for config blocks.
            cli.out(_indent(yaml_util.encode_yaml(item_val), 4))
        else:
            cli.out(f"  {item_name}: {flag_util.encode_flag_val(item_val)}")


def _sort_run_info_attr(name, val):
    if name == "scalars":
        return _sort_run_info_scalars(val)
    return util.natsorted(val.items())


def _sort_run_info_scalars(val):
    key = lambda item: _split_scalar_key(item[0])
    return sorted(val.items(), key=key)


def _indent(s, spaces):
    prefix = " " * spaces
    return "\n".join([f"{prefix}{line}" for line in s.split("\n")])


def _fix_quoted_string(s):
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    return s


def _unindent(s):
    return "\n".join([line.strip() for line in s.split("\n")])


def label(args, ctx):
    _check_label_args(args, ctx)
    if args.remote:
        remote_impl_support.label_runs(args)
    else:
        _set_labels(args, ctx)


def _check_label_args(args, ctx):
    cmd_impl_support.check_required_args(
        [
            "set",
            "append",
            "prepend",
            "remove",
            "clear",
        ],
        args,
        ctx,
    )
    cmd_impl_support.check_incompatible_args(
        [
            ("set", "append"),
            ("set", "prepend"),
            ("set", "remove"),
            ("set", "clear"),
            ("append", "prepend"),
            ("append", "clear"),
            ("append", "remove"),
            ("prepend", "clear"),
            ("prepend", "remove"),
        ],
        args,
        ctx,
    )


def _set_labels(args, ctx):
    preview = _set_labels_preview(args)
    confirm = "Continue?"
    no_runs = "No runs to modify."

    def set_labels(selected):
        for run in selected:
            if args.clear:
                run.del_attr("label")
            else:
                run.write_attr("label", _label_for_run(run, args).strip())
        if args.clear:
            cli.out(f"Cleared label for {len(selected)} run(s)", err=True)
        else:
            cli.out(f"Labeled {len(selected)} run(s)", err=True)

    runs_op(args, ctx, preview, confirm, no_runs, set_labels, LATEST_RUN_ARG, True)


def _set_labels_preview(args):
    if args.set:
        return f"You are about to label the following runs with '{args.set}':"
    if args.prepend:
        return (
            f"You are about to prepend '{args.prepend}' to the label of "
            "the following runs:"
        )
    if args.append:
        return (
            f"You are about to append '{args.append}' to the label of "
            "the following runs:"
        )
    if args.remove:
        return (
            f"You are about to remove '{args.remove}' from the label of "
            "the following runs:"
        )
    if args.clear:
        return "You are about to clear the label of the following runs:"
    assert False, args


def _label_for_run(run, args):
    if args.set:
        return format_run_label(args.set, run)
    if args.prepend:
        return f"{format_run_label(args.prepend, run)} {_run_label(run)}"
    if args.append:
        return f"{_run_label(run)} {format_run_label(args.append, run)}"
    if args.remove:
        return _remove_label_parts(args.remove, _run_label(run))
    assert False, args


def format_run_label(template, run):
    fmt_params = run.get("flags") or {}
    fmt_params["label"] = _run_label(run)
    return op_util.run_label(template, fmt_params).strip()


def _run_label(run):
    return run.get("label") or ""


def _remove_label_parts(parts, label):
    for part in parts:
        label = _remove_label_part(part, label)
    return label


def _remove_label_part(part, label):
    try:
        split_parts = re.split(rf"(^|\s){part}($|\s)", label)
    except Exception as e:
        cli.error(f"cannot remove label part {part!r}: {e}")
    else:
        return " ".join([s for s in [t.strip() for t in split_parts] if s])


def stop_runs(args, ctx=None):
    if args.remote:
        remote_impl_support.stop_runs(args)
    else:
        _stop_runs(args, ctx)


def _stop_runs(args, ctx):
    preview = cmd_impl_support.format_warn("You are about to stop the following runs:")
    confirm = "Stop {count} run(s)?"
    no_runs_help = "Nothing to stop."
    if not args.runs:
        args.status_running = True

    def stop_f(selected):
        for run in selected:
            _stop_run(
                run,
                no_wait=args.no_wait,
                force=args.force,
                timeout=args.timeout,
            )

    def select_runs_f(args, ctx, default_runs_arg):
        runs = runs_op_selected(args, ctx, default_runs_arg)
        return [run for run in runs if not run.remote]

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs_help,
        stop_f,
        None,
        False,
        select_runs_f,
    )


def _stop_run(run, no_wait=False, force=False, timeout=None):
    remote_lock = remote_run_support.lock_for_run(run)
    if remote_lock:
        _try_stop_remote_run(run, remote_lock, no_wait)
    else:
        _try_stop_local_run(run, force=force, timeout=timeout)


def _try_stop_remote_run(run, remote_lock, no_wait):
    from guild import plugin as pluginlib  # expensive

    try:
        plugin = pluginlib.for_name(remote_lock.plugin_name)
    except LookupError:
        log.warning(
            "error syncing run '%s': plugin '%s' not available",
            run.id,
            remote_lock.plugin_name,
        )
    else:
        cli.out(f"Stopping {run.id} (remote)", err=True)
        plugin.stop_run(run, {"no_wait": no_wait})


def _try_stop_local_run(run, force=False, timeout=None):
    pid = run.pid
    if not pid or not util.pid_exists(pid):
        cli.out(f"Run {run.id} is not running")
        return
    cli.out(f"Stopping {run.id} (pid {run.pid})", err=True)
    alive_pids = run_util.stop_run(pid, force=force, timeout=timeout)
    if alive_pids:
        _unstopped_process_error(alive_pids)


def _unstopped_process_error(pids) -> typing.NoReturn:
    alive_desc = ", ".join([str(pid) for pid in pids])
    cli.out(f"The following processes did not stop as expected: {alive_desc}")
    cli.error()


def export(args, ctx):
    export_desc = "move" if args.move else "copy"
    preview = f"You are about to {export_desc} the following runs to '{args.location}':"
    confirm = "Continue?"
    no_runs = "No runs to export."

    def export_f(selected):
        if args.copy_resources and not args.yes:
            cli.out(
                cmd_impl_support.format_warn(
                    "WARNING: You specified --copy-resources, which will "
                    "copy resources used by each run."
                ),
                err=True,
            )
            if not cli.confirm("Really copy resources exported runs?"):
                raise SystemExit(exit_code.ABORTED)
        try:
            exported = run_util.export_runs(
                selected,
                args.location,
                move=args.move,
                copy_resources=args.copy_resources,
            )
        except run_util.RunsExportError as e:
            cli.error(e.args[0])
        else:
            cli.out(f"Exported {len(exported)} run(s) to {args.location}", err=True)

    runs_op(args, ctx, preview, confirm, no_runs, export_f, ALL_RUNS_ARG, True)


def import_(args, ctx):
    archive_path = _validated_archive_path(args.archive)
    if _is_zip_archive(archive_path):
        if args.move:
            cli.error("'--move' cannot be used with zip archives")
    elif os.path.isfile(archive_path):
        cli.error(
            f"invalid archive {args.archive} - expected a directory or a zip file"
        )
    import_desc = "move" if args.move else "copy"
    preview = (
        f"You are about to import ({import_desc}) the following "
        f"runs from '{args.archive}':"
    )
    confirm = "Continue?"
    no_runs = "No runs to import."

    def import_f(selected):
        if args.copy_resources and not args.yes:
            cli.out(
                cmd_impl_support.format_warn(
                    "WARNING: You specified --copy-resources, which will "
                    "copy resources used by each run."
                ),
                err=True,
            )
            if not cli.confirm("Really copy resources exported runs?"):
                raise SystemExit(exit_code.ABORTED)
        try:
            imported = run_util.import_runs(
                selected,
                move=args.move,
                copy_resources=args.copy_resources,
            )
        except run_util.RunsImportError as e:
            cli.error(e.args[0])
        cli.out(f"Imported {len(imported)} run(s) from {args.archive}", err=True)

    runs_op(args, ctx, preview, confirm, no_runs, import_f, ALL_RUNS_ARG, True)


def _is_zip_archive(path):
    return path.lower().endswith(".zip")


def push(args, ctx):
    preview = (
        f"You are about to copy (push{_delete_clause(args)}) the "
        f"following runs to {args.remote}:"
    )
    confirm = "Continue?"
    no_runs = "No runs to copy."

    def push_f(runs):
        remote_impl_support.push_runs(runs, args)

    runs_op(
        args.copy(remote=None),
        ctx,
        preview,
        confirm,
        no_runs,
        push_f,
        ALL_RUNS_ARG,
        True,
    )


def _delete_clause(args):
    if args.delete:
        return " with delete"
    return ""


def pull(args, ctx):
    preview = (
        f"You are about to copy (pull{_delete_clause(args)}) the "
        f"following runs from {args.remote}:"
    )
    confirm = "Continue?"
    no_runs = "No runs to copy."

    def pull_f(runs):
        remote_impl_support.pull_runs(runs, args)

    def filtered_runs_f(args, _ctx, _default_runs_arg):
        filtered = remote_impl_support.filtered_runs(args)
        return select_runs(filtered, args.runs, ctx)

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs,
        pull_f,
        ALL_RUNS_ARG,
        True,
        filtered_runs_f,
    )


def mark(args, ctx=None):
    if args.clear:
        _clear_marked(args, ctx)
    else:
        _mark(args, ctx)


def _clear_marked(args, ctx):
    preview = "You are about to unmark the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to unmark."

    def clear(selected):
        for run in selected:
            run.del_attr("marked")
        cli.out(f"Unmarked {len(selected)} run(s)", err=True)

    if not args.runs:
        args.filter_marked = True
    runs_op(args, ctx, preview, confirm, no_runs, clear, ALL_RUNS_ARG, True)


def _mark(args, ctx):
    preview = "You are about to mark the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to mark."

    def mark(selected):
        for run in selected:
            run.write_attr("marked", True)
        cli.out(f"Marked {len(selected)} run(s)", err=True)

    if not args.runs:
        args.filter_marked = True
    runs_op(args, ctx, preview, confirm, no_runs, mark, LATEST_RUN_ARG, True)


def select(args, ctx):
    if args.remote:
        remote_impl_support.select(args)
    else:
        _select(args, ctx)


def _select(args, ctx):
    _check_select_args(args, ctx)
    _maybe_apply_select_all(args)
    if args.all:
        _print_all_selected_runs(args, ctx)
    else:
        _print_latest_selected_run(args, ctx)


def _check_select_args(args, ctx):
    cmd_impl_support.check_incompatible_args(
        [
            ("short_id", "attr"),
            ("min", "max"),
        ],
        args,
        ctx,
    )


def _maybe_apply_select_all(args):
    if len(args.runs) > 1 and not args.min and not args.max:
        args.all = True
    elif args.min or args.max:
        args.all = False


def _print_all_selected_runs(args, ctx):
    for run in _select_runs(args, ctx):
        _print_select_info(run, args)


def _print_latest_selected_run(args, ctx):
    run = select_run(args, ctx)
    _print_select_info(run, args)


def select_run(args, ctx=None):
    _check_select_run_args(args, ctx)
    if args.min:
        return _select_min_run(args, ctx, args.min)
    if args.max:
        return _select_min_run(args, ctx, args.max, reverse=True)
    args.run = args.runs[0] if args.runs else None
    return one_run(args, ctx)


def _check_select_run_args(args, ctx):
    cmd_impl_support.check_incompatible_args([("min", "max")], args, ctx)


def _select_min_run(args, ctx, colspec, reverse=False):
    runs = _select_runs(args, ctx)
    assert runs  # _select_runs exits early if nothing matches.
    return _sort_selected_runs(runs, colspec, reverse)[0]


def _select_runs(args, ctx):
    return runs_for_args(args, ctx=ctx)


def _sort_selected_runs(runs, colspec, reverse):
    from guild import index as indexlib  # expensive

    colspec_val_for_run = _colspec_val_f(colspec)

    index = indexlib.RunIndex()
    index.refresh(runs, ["scalar", "flag", "attr"])

    def key(run):
        val = colspec_val_for_run(run, index)
        log.debug("got %r for '%s' for run %s", val, colspec, run.id)
        return val

    return util.natsorted(runs, key=key, reverse=reverse)


def _colspec_val_f(colspec):
    from guild import query

    try:
        cols = query.parse_colspec(colspec).cols
    except query.ParseError as e:
        cli.error(f"invalid col spec '{colspec}': {e}")
    else:
        assert cols, colspec
        if len(cols) > 1:
            cli.error(f"invalid col spec '{colspec}': multiple cols not supported")
        col = cols[0]
        if isinstance(col, query.Scalar):
            return _scalar_val_f(col)
        if isinstance(col, query.Flag):
            return _flag_val_f(col)
        if isinstance(col, query.Attr):
            return _attr_val_f(col)
        assert False, col


def _scalar_val_f(col):
    if col.named_as:
        log.warning("ignoring 'as %s' in scalar", col.named_as)
    prefix, tag = col.split_key()

    def f(run, index):
        return index.run_scalar(run, prefix, tag, col.qualifier, col.step)

    return f


def _flag_val_f(col):
    def f(run, index):
        return index.run_flag(run, col.name)

    return f


def _attr_val_f(col):
    def f(run, index):
        return index.run_attr(run, col.name)

    return f


def _print_select_info(run, args):
    if args.attr:
        _print_run_attr(run, args.attr)
    elif args.short_id:
        print(run.short_id)
    elif args.path:
        print(run.dir)
    else:
        print(run.id)


def _print_run_attr(run, attr_name):
    util.try_apply(
        [
            lambda: _try_print_formatted_run_attr(run, attr_name),
            lambda: _try_print_raw_run_attr(run, attr_name),
            lambda: _no_such_run_attr_error(attr_name),
        ]
    )


def _try_print_formatted_run_attr(run, attr_name):
    formatted = run_util.format_run(run)
    try:
        val = formatted[attr_name]
    except KeyError as e:
        raise util.TryFailed() from e
    else:
        print(val)


def _try_print_raw_run_attr(run, attr_name):
    try:
        val = run[attr_name]
    except KeyError as e:
        raise util.TryFailed() from e
    else:
        print(yaml_util.encode_yaml(val))


def _no_such_run_attr_error(attr_name):
    cli.error(f"no such run attribute '{attr_name}'")


def tag(args, ctx):
    _check_tag_args(args, ctx)
    if args.remote:
        remote_impl_support.tag_runs(args)
    else:
        if args.list_all:
            _list_all_tags(args, ctx)
        else:
            _set_tags(args, ctx)


def _check_tag_args(args, ctx):
    cmd_impl_support.check_required_args(
        [
            "add",
            "delete",
            "clear",
            "list_all",
        ],
        args,
        ctx,
    )
    cmd_impl_support.check_incompatible_args(
        [
            ("add", "list_all"),
            ("delete", "list_all"),
            ("clear", "list_all"),
        ],
        args,
        ctx,
    )


def _list_all_tags(args, ctx):
    selected = runs_op_selected(args, ctx, ALL_RUNS_ARG)
    tags = set()
    for run in selected:
        tags.update(_run_tags(run))
    for tag in sorted(tags):
        print(tag)


def _run_tags(run):
    tags = run.get("tags")
    if not tags:
        return []
    try:
        return list(tags)
    except Exception as e:
        log.warning("Error reading tags for run %s: %s", run.id, e)
        return []


def _set_tags(args, ctx):
    preview = _set_tags_preview(args)
    confirm = "Continue?"
    no_runs = "No runs to modify."

    def set_tags(selected):
        for run in selected:
            old_tags = _run_tags(run)
            new_tags = _tags_for_run(old_tags, args)
            run.write_attr("tags", new_tags)
            if args.sync_labels:
                new_label = _synced_label_for_tags(run, old_tags, args)
                run.write_attr("label", new_label)
        cli.out(f"Modified tags for {len(selected)} run(s)", err=True)

    runs_op(args, ctx, preview, confirm, no_runs, set_tags, LATEST_RUN_ARG, True)


def _set_tags_preview(args):
    lines = ["You are about to modify tags for the following runs:"]
    lines.append(_labels_sync_desc(args))
    return "\n".join(lines)


def _labels_sync_desc(args):
    if args.sync_labels:
        return cmd_impl_support.format_warn(
            "Labels are updated to reflect the latest tags."
        )
    return cmd_impl_support.format_warn(
        "Labels are not updated - use --sync-labels to "
        "apply changes run labels."
    )


def _tags_for_run(old_tags, args):
    tags = set(old_tags or [])
    tags.difference_update(old_tags if args.clear else args.delete)
    tags.update(args.add)
    return sorted(tags)


def _synced_label_for_tags(run, old_tags, args):
    tags_to_delete = set(old_tags if args.clear else args.delete)
    old_label = run.get("label") or ""
    new_label = _remove_label_parts(tags_to_delete, old_label)
    tags_to_prepend = _tags_not_in_label(args.add, old_label)
    joined_tags = " ".join(tags_to_prepend)
    if tags_to_prepend:
        new_label = f"{joined_tags} {new_label}"
    return new_label


def _tags_not_in_label(tags, label):
    if not tags:
        return []
    label_parts = util.shlex_split(label)
    return [tag for tag in tags if tag not in label_parts]


def comment(args, ctx):
    if args.remote:
        _check_comment_args_for_remote(args, ctx)
        remote_impl_support.comment_runs(args)
    else:
        _check_comment_args(args, ctx)
        _comment(args, ctx)


def _check_comment_args_for_remote(args, ctx):
    _check_comment_args(args, ctx)
    cmd_impl_support.check_incompatible_args(
        [
            ("remote", "edit"),
        ],
        args,
        ctx,
    )
    cmd_impl_support.check_required_args(
        [
            "list",
            "add",
            "delete",
            "clear",
        ],
        args,
        ctx,
        msg_template="--remote option required on of: %s",
    )


def _check_comment_args(args, ctx):
    cmd_impl_support.check_incompatible_args(
        [
            ("list", "add"),
            ("list", "delete"),
            ("list", "clear"),
            ("add", "delete"),
            ("add", "clear"),
            ("edit", "delete"),
            ("edit", "clear"),
            ("delete", "clear"),
        ],
        args,
        ctx,
    )


def _comment(args, ctx):
    if args.list:
        _list_comments(args, ctx)
    elif args.delete:
        _delete_comment(args.delete, args, ctx)
    elif args.clear:
        _clear_comments(args, ctx)
    else:
        _add_comment(args, ctx)


def _list_comments(args, ctx):
    _list_runs_comments(runs_op_selected(args, ctx, LATEST_RUN_ARG), args)


def _list_runs_comments(runs, args, comment_index_format=True):
    formatted_runs = format_runs(runs)
    cols = _cols_for_list_with_comments(comment_index_format, args)
    cli.table(
        formatted_runs,
        cols,
        detail=["_run"],
        detail_cb=_run_comments_detail_cb(comment_index_format),
        max_width_adj=STYLE_TABLE_WIDTH_ADJ,
        fg=_fg_for_comments_header(comment_index_format),
    )


def _cols_for_list_with_comments(comment_index_format, args):
    if not comment_index_format:
        return _cols_for_list(args)
    return [
        "short_id",
        "op_desc",
        "started",
        "status_with_remote",
        "label",
    ]


def _fg_for_comments_header(comment_index_format):
    if comment_index_format:
        return "yellow"
    return None


def _run_comments_detail_cb(comment_index_format):
    def f(formatted_run):
        run = formatted_run["_run"]
        comments = run.get("comments")
        if comments:
            index = 1
            for comment in comments:
                _print_comment(index, comment, comment_index_format)
                index += 1
        else:
            _print_no_comments(comment_index_format)

    return f


def _print_comment(index, comment, comment_index_format):
    from guild import help

    out = help.ConsoleFormatter()
    out.write_text(_format_comment_header(index, comment, comment_index_format))
    out.write_paragraph()
    if comment_index_format:
        out.indent()
    else:
        out.indent()
        out.indent()
    out.write_text(_format_comment_body(comment))
    cli.out("".join(out.buffer))


def _format_comment_header(index, comment, comment_index_format):
    user = _format_comment_user(comment)
    time = _format_comment_time(comment)
    if comment_index_format:
        return f"[{index}] {user} {time}"
    return f"  {user} {time}"


def _format_comment_user(comment):
    user = comment.get("user") or ""
    host = comment.get("host") or ""
    if not host:
        return user
    return f"{user}@{host}"


def _format_comment_time(comment):
    time_attr = comment.get("time")
    try:
        return util.format_timestamp(time_attr)
    except (ValueError, TypeError):
        return str(time_attr)


def _format_comment_body(comment):
    return comment.get("body") or ""


def _print_no_comments(comment_index_format):
    if comment_index_format:
        cli.out("  <no comments>")


def _delete_comment(comment_index, args, ctx):
    preview = (
        f"You are about to delete comment {comment_index} from the following runs:"
    )
    confirm = "Continue?"
    no_runs = "No runs to modify."

    def delete_comments(selected):
        for run in selected:
            new_comments = _delete_run_comment(run, comment_index)
            run.write_attr("comments", new_comments)
        cli.out(f"Deleted comment for {len(selected)} run(s)", err=True)

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs,
        delete_comments,
        LATEST_RUN_ARG,
        True,
    )


def _delete_run_comment(run, comment_index):
    comments = run.get("comments")
    try:
        del comments[comment_index - 1]
    except IndexError:
        pass
    return comments


def _clear_comments(args, ctx):
    preview = cmd_impl_support.format_warn(
        "WARNING: You are about to delete ALL comments from the following runs:"
    )
    confirm = "Continue?"
    no_runs = "No runs to modify."

    def clear_comments(selected):
        for run in selected:
            run.del_attr("comments")
        cli.out(f"Deleted all comments for {len(selected)} run(s)", err=True)

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs,
        clear_comments,
        LATEST_RUN_ARG,
    )


def _add_comment(args, ctx):
    runs = runs_op_selected(args, ctx, LATEST_RUN_ARG)
    comment, edited = _comment_for_args(args, runs)
    if not comment:
        cli.out("Aborting due to an empty comment.", err=True)
        cli.error()

    def add_comment(selected):
        for run in selected:
            new_comments = _add_run_comment(run, comment, args.user)
            run.write_attr("comments", new_comments)
        cli.out(f"Added comment to {len(selected)} run(s)", err=True)

    if edited:
        # Skip prompt below because the editor serves as a prompt.
        add_comment(runs)
        return

    preview = "You are about to add a comment to the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to modify."

    runs_op(
        args,
        ctx,
        preview,
        confirm,
        no_runs,
        add_comment,
        LATEST_RUN_ARG,
        True,
        lambda *_args: runs,
    )


def _comment_for_args(args, runs):
    comment = args.add
    edited = False
    if not comment or args.edit:
        comment = _get_comment_with_editor(comment, runs)
        edited = True
    return comment.strip(), edited


def _get_comment_with_editor(initial_comment, runs):
    msg_lines = [
        initial_comment or "",
        "# Type a comment for the runs below. Lines starting with '#' are ",
        "# ignored. An empty comment aborts the command.",
        "#",
        "# Runs:",
    ]
    formatted_runs = _format_runs_for_comment_msg(runs)
    msg_lines.extend([f"#  {line}" for line in formatted_runs.split("\n")])
    return util.edit(
        "\n".join(msg_lines),
        extension=".GUILD_COMMENT",
        strip_comment_lines=True,
    )


def _format_runs_for_comment_msg(runs):
    out = io.StringIO()
    formatted = format_runs(runs)
    cols = [
        "short_index",
        "op_desc",
        "started",
        "status_with_remote",
        "label",
    ]
    cli.table(formatted, cols, indent=2, file=out)
    return out.getvalue().strip()


def _add_run_comment(run, comment, user):
    from . import run_impl

    comments = run.get("comments") or []
    if user:
        user, host = _split_comment_user(user)
        if not host:
            host = util.hostname()
    else:
        user = util.user()
        host = util.hostname()
    comments.append(
        {
            "body": comment,
            "user": user,
            "host": host,
            "time": run_impl.comment_timestamp(),
        }
    )
    return comments


def _split_comment_user(user):
    parts = user.split("@", 1)
    if len(parts) == 2:
        return parts
    return parts[0], None


def archive(args, ctx):
    if args.list:
        _print_archives(args)
        raise SystemExit(0)
    if not args.name:
        cli.error("missing argument for NAME")

    archive = _archive_for_name(args.name)
    if not archive and not args.create:
        cli.error(
            f"archive '{args.name}' does not exist\n"
            f"Try '{ctx.command_path} --list' to list available archives "
            "or use the '--create' option."
        )

    archive_desc = "copy" if args.copy else "move"
    preview = (
        f"You are about to archive ({archive_desc}) the following "
        f"runs to '{args.name}':"
    )
    confirm = "Continue?"
    no_runs = "No runs to archive."

    def archive_f(selected):
        dest_dir = archive.path if archive else _create_archive(args)
        if not os.path.exists(dest_dir):
            cli.error(
                f"archive directory {dest_dir} no longer exists\n"
                "Try the command with a different archive or use '--create'."
            )

        try:
            archived = run_util.export_runs(
                selected,
                dest_dir,
                move=not args.copy,
                copy_resources=args.copy_resources,
            )
        except run_util.RunsExportError as e:
            cli.error(e.args[0])
        else:
            cli.out(f"Archived {len(archived)} run(s) to '{args.name}'", err=True)

    runs_op(args, ctx, preview, confirm, no_runs, archive_f, ALL_RUNS_ARG, True)


def _archive_for_name(name):
    matching = [a for a in config.archives() if name in (a.label, a.name == name)]
    return matching[0] if matching else None


def _create_archive(args):
    assert args.name
    assert args.create

    id = uuid.uuid4().hex
    archive_dir = os.path.join(config.archives_home(), id)

    cli.out(f"Creating '{args.name}'")

    util.ensure_dir(archive_dir)
    with open(os.path.join(archive_dir, "archive.json"), "w") as f:
        json.dump(
            {
                "label": args.name,
                **({
                    "description": args.description
                } if args.description else {})
            }, f
        )
    return archive_dir


def _print_archives(args):
    cli.table(
        [
            {
                "name": a.label or a.name,
                "desc": a.get_metadata("description") or "",
                "path": util.format_user_dir(a.path),
            } for a in sorted(config.archives(), key=lambda a: a.label or a.name)
        ],
        cols=["name", "desc"],
        detail=["path"] if args.verbose else []
    )
