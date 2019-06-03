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

import inspect
import json
import logging
import os
import re
import shutil
import signal

import guild.opref

from guild import batch_util
from guild import cli
from guild import cmd_impl_support
from guild import index2 as indexlib
from guild import publish as publishlib
from guild import remote_run_support
from guild import run as runlib
from guild import run_util
from guild import util
from guild import var

from . import remote_support
from . import remote_impl_support

log = logging.getLogger("guild")

RUN_DETAIL = [
    "id",
    "operation",
    "status",
    "started",
    "stopped",
    "marked",
    "label",
    "run_dir",
    "command",
    "exit_status",
    "pid",
]

ALL_RUNS_ARG = [":"]
LATEST_RUN_ARG = ["1"]

CORE_RUN_ATTRS = [
    "cmd",
    "compare",
    "deps",
    "env",
    "exit_status",
    "exit_status.remote",
    "flags",
    "host",
    "id",
    "initialized",
    "label",
    "marked",
    "objective",
    "opdef",
    "random_seed",
    "run_params",
    "started",
    "stopped",
    "user",
]

RUNS_PER_GROUP = 20

FILTERABLE = [
    "completed",
    "error",
    "pending",
    "running",
    "terminated",
]

def runs_for_args(args, ctx=None, force_deleted=False):
    filtered = filtered_runs(args, force_deleted)
    return select_runs(filtered, args.runs, ctx)

def filtered_runs(args, force_deleted=False):
    return var.runs(
        _runs_root_for_args(args, force_deleted),
        sort=["-timestamp"],
        filter=_runs_filter(args))

def _runs_root_for_args(args, force_deleted):
    archive = getattr(args, "archive", None)
    if archive:
        if not os.path.exists(archive):
            cli.error("archive directory '%s' does not exist" % archive)
        return archive
    deleted = force_deleted or getattr(args, "deleted", False)
    return var.runs_dir(deleted=deleted)

def _runs_filter(args):
    filters = []
    _apply_status_filter(args, filters)
    _apply_ops_filter(args, filters)
    _apply_labels_filter(args, filters)
    _apply_marked_filter(args, filters)
    return var.run_filter("all", filters)

def _apply_status_filter(args, filters):
    status_filters = [
        var.run_filter("attr", "status", status)
        for status in FILTERABLE
        if getattr(args, status, False)
    ]
    if status_filters:
        filters.append(var.run_filter("any", status_filters))

def _apply_ops_filter(args, filters):
    if args.ops:
        filters.append(_op_run_filter(args.ops))

def _op_run_filter(op_refs):
    def f(run):
        op_desc = run_util.format_op_desc(run, nowarn=True)
        return any((ref in op_desc for ref in op_refs))
    return f

def _apply_labels_filter(args, filters):
    if args.labels and args.unlabeled:
        cli.error("--label and --unlabeled cannot both be used")
    if args.labels:
        filters.append(_label_filter(args.labels))
    elif args.unlabeled:
        filters.append(_unlabeled_filter())

def _label_filter(labels):
    def f(run):
        return any((l in run.get("label", "") for l in labels))
    return f

def _unlabeled_filter():
    def f(run):
        return not run.get("label", "").strip()
    return f

def _apply_marked_filter(args, filters):
    if args.marked and args.unmarked:
        cli.error("--marked and --unmarked cannot both be used")
    if args.marked:
        filters.append(_marked_filter())
    if args.unmarked:
        filters.append(_marked_filter(False))

def _marked_filter(test_for=True):
    def f(run):
        marked = bool(run.get("marked"))
        return marked if test_for is True else not marked
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
    except ValueError:
        m = re.match("(\\d+)?:(\\d+)?", spec)
        if m:
            try:
                return (
                    _slice_part(m.group(1), decr=True),
                    _slice_part(m.group(2))
                )
            except ValueError:
                pass
        raise ValueError(spec)
    else:
        return index - 1, index

def _slice_part(s, decr=False):
    if s is None:
        return None
    elif decr:
        return int(s) - 1
    else:
        return int(s)

def _find_run_by_id(id_part, runs, ctx):
    matches = [run for run in runs if run.id.startswith(id_part)]
    return cmd_impl_support.one_run(matches, id_part, ctx)

def _in_range(slice_start, slice_end, l):
    return (
        (slice_start is None or slice_start >= 0) and
        (slice_end is None or slice_end <= len(l))
    )

def list_runs(args):
    if args.remote:
        remote_impl_support.list_runs(args)
    else:
        _list_runs(args)

def _list_runs(args):
    if args.archive and args.deleted:
        cli.error("--archive and --deleted may not both be used")
    runs = filtered_runs(args)
    if args.json:
        if args.more or args.all:
            cli.note("--json option always shows all runs")
        _list_runs_json(runs)
    else:
        _list_formatted_runs(runs, args)

def _list_runs_json(runs):
    runs_data = [_listed_run_json_data(run) for run in runs]
    cli.out(json.dumps(runs_data))

def _listed_run_json_data(run):
    return _run_data(run, (
        "exit_status",
        "cmd",
        "marked",
        "label",
        "started",
        "status",
        "stopped",
    ))

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
    else:
        return run.get(name)

def _list_formatted_runs(runs, args):
    formatted = []
    for i, run in enumerate(runs):
        try:
            formatted_run = run_util.format_run(run, i + 1)
        except Exception:
            log.exception("formatting run in %s", run.path)
        else:
            formatted.append(formatted_run)
    limited_formatted = _limit_runs(formatted, args)
    cols = [
        "index",
        "operation_with_marked",
        "started",
        "status_with_remote",
        "label"]
    detail = RUN_DETAIL if args.verbose else None
    cli.table(limited_formatted, cols=cols, detail=detail)

def _limit_runs(runs, args):
    if args.all:
        return runs
    limited = runs[:(args.more + 1) * RUNS_PER_GROUP]
    if len(limited) < len(runs):
        cli.note(
            "Showing the first %i runs (%i total) - use --all "
            "to show all or -m to show more"
            % (len(limited), len(runs)))
    return limited

def _no_selected_runs_exit(help_msg=None):
    help_msg = (
        help_msg or
        "No matching runs\n"
        "Try 'guild runs list' to list available runs."
    )
    cli.out(help_msg, err=True)
    raise SystemExit(0)

def _runs_op(args, ctx, force_deleted, preview_msg, confirm_prompt,
             no_runs_help, op_callback, default_runs_arg=None,
             confirm_default=False, runs_callback=None):
    get_selected = runs_callback or _runs_op_selected
    selected = get_selected(args, ctx, default_runs_arg, force_deleted)
    if not selected:
        _no_selected_runs_exit(no_runs_help)
    formatted = [run_util.format_run(run) for run in selected]
    if not args.yes:
        cli.out(preview_msg)
        cols = [
            "short_index", "operation_with_marked", "started",
            "status_with_remote", "label"]
        cli.table(formatted, cols=cols, indent=2)
    formatted_confirm_prompt = confirm_prompt.format(count=len(formatted))
    if args.yes or cli.confirm(formatted_confirm_prompt, confirm_default):
        if len(inspect.getargspec(op_callback).args) == 2:
            op_callback(selected, formatted)
        else:
            op_callback(selected)

def _runs_op_selected(args, ctx, default_runs_arg, force_deleted):
    default_runs_arg = default_runs_arg or ALL_RUNS_ARG
    runs_arg = _remove_duplicates(args.runs or default_runs_arg)
    filtered = filtered_runs(args, force_deleted)
    return select_runs(filtered, runs_arg, ctx)

def _remove_duplicates(vals):
    deduped = []
    for val in vals:
        if val not in deduped:
            deduped.append(val)
    return deduped

def delete_runs(args, ctx):
    if args.remote:
        remote_impl_support.delete_runs(args)
    else:
        _delete_runs(args, ctx)

def _delete_runs(args, ctx):
    if args.permanent:
        preview = (
            "WARNING: You are about to permanently delete "
            "the following runs:")
        confirm = "Permanently delete {count} run(s)?"
    else:
        preview = "You are about to delete the following runs:"
        confirm = "Delete {count} run(s)?"
    no_runs_help = "Nothing to delete."
    def delete(selected):
        stoppable = [
            run for run in selected
            if run.status == "running" and not run.remote]
        if stoppable and not args.yes:
            cli.out(
                "WARNING: one or more runs are still running "
                "and will be stopped before being deleted.")
            if not cli.confirm("Really delete these runs?"):
                return
        for run in stoppable:
            _stop_run(run, no_wait=True)
        var.delete_runs(selected, args.permanent)
        if args.permanent:
            cli.out("Permanently deleted %i run(s)" % len(selected))
        else:
            cli.out("Deleted %i run(s)" % len(selected))
    _runs_op(
        args, ctx, False, preview, confirm, no_runs_help,
        delete, confirm_default=not args.permanent)

def purge_runs(args, ctx):
    if args.remote:
        remote_impl_support.purge_runs(args)
    else:
        _purge_runs(args, ctx)

def _purge_runs(args, ctx):
    preview = (
        "WARNING: You are about to permanently delete "
        "the following runs:")
    confirm = "Permanently delete {count} run(s)?"
    no_runs_help = "Nothing to purge."
    def purge(selected):
        var.purge_runs(selected)
        cli.out("Permanently deleted %i run(s)" % len(selected))
    _runs_op(args, ctx, True, preview, confirm, no_runs_help, purge)

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
        cli.out("Restored %i run(s)" % len(selected))
    _runs_op(
        args, ctx, True, preview, confirm, no_runs_help,
        restore, confirm_default=True)

def run_info(args, ctx):
    if args.remote:
        remote_impl_support.run_info(args)
    else:
        _run_info(args, ctx)

def _run_info(args, ctx):
    run = one_run(args, ctx)
    if args.page_output:
        _page_run_output(run)
    else:
        _print_run_info(run, args)

def one_run(args, ctx):
    filtered = filtered_runs(args)
    if not filtered:
        cli.out("No matching runs", err=True)
        cli.error()
    runspec = args.run or "1"
    selected = select_runs(filtered, [runspec], ctx)
    return cmd_impl_support.one_run(selected, runspec, ctx)

def _page_run_output(run):
    reader = util.RunOutputReader(run.path)
    lines = []
    try:
        lines = reader.read()
    except IOError as e:
        cli.error("error reading output for run %s: %s" % (run.id, e))
    lines = [_format_output_line(stream, line) for _time, stream, line in lines]
    cli.page("\n".join(lines))

def _format_output_line(stream, line):
    if stream == 1:
        return cli.style(line, fg="red")
    return line

def _print_run_info(run, args):
    formatted = run_util.format_run(run)
    out = cli.out
    for name in RUN_DETAIL:
        out("%s: %s" % (name, formatted[name]))
    for name in other_attr_names(run, args.private_attrs):
        out("%s: %s" % (name, run_util.format_attr(run.get(name))))
    out("flags:", nl=False)
    out(run_util.format_attr(run.get("flags", "")).rstrip())
    _maybe_print_proto_flags(run, out)
    if args.env:
        out("environment:", nl=False)
        out(run_util.format_attr(run.get("env", "")))
    if args.scalars:
        out("scalars:")
        for scalar in _iter_scalars(run):
            out("  %s" % scalar)
    if args.deps:
        out("dependencies:")
        deps = run.get("deps", {})
        for name in sorted(deps):
            out("  %s:" % name)
            for path in deps[name]:
                out("    %s" % path)
    if args.sourcecode:
        out("sourcecode:")
        for path in sorted(run.iter_guild_files("sourcecode")):
            out("  %s" % path)
    if args.output:
        out("output:")
        for line in run_util.iter_output(run):
            out("  %s" % line, nl=False)
    if args.files or args.all_files:
        out("files:")
        for path in sorted(run.iter_files(args.all_files, args.follow_links)):
            if args.files == 1:
                path = os.path.relpath(path, run.path)
            out("  %s" % path)

def other_attr_names(run, include_private=False):
    if include_private:
        include = lambda x: x not in CORE_RUN_ATTRS
    else:
        include = lambda x: x[0] != "_" and x not in CORE_RUN_ATTRS
    return [name for name in sorted(run.attr_names()) if include(name)]

def _maybe_print_proto_flags(run, out):
    proto_dir = run.guild_path("proto")
    if os.path.exists(proto_dir):
        proto_run = runlib.Run("", proto_dir)
        out("proto-flags:", nl=False)
        out(run_util.format_attr(proto_run.get("flags", "")))

def _iter_scalars(run):
    for s in indexlib.iter_run_scalars(run):
        yield "%s: %f (step %i)" % (_s_key(s), _s_val(s), _s_step(s))

def _s_key(s):
    prefix = s["prefix"]
    if prefix:
        return "%s#%s" % (s["prefix"], s["tag"])
    else:
        return s["tag"]

def _s_val(s):
    return s["last_val"]

def _s_step(s):
    return s["last_step"]

def label(args, ctx):
    if args.remote:
        remote_impl_support.label_runs(args)
    else:
        _label(args, ctx)

def _label(args, ctx):
    if args.clear:
        _clear_labels(args, ctx)
    elif args.label:
        _set_labels(args, ctx)
    else:
        cli.error("specify a label")

def _clear_labels(args, ctx):
    # if a label arg is provided, assume it's a run spec
    if args.label:
        args.runs += (args.label,)
    preview = "You are about to clear the labels for the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to modify."
    def clear_labels(selected):
        for run in selected:
            run.del_attr("label")
        cli.out("Cleared label for %i run(s)" % len(selected))
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        clear_labels, LATEST_RUN_ARG, True)

def _set_labels(args, ctx):
    preview = (
        "You are about to label the following runs with '%s':"
        % args.label)
    confirm = "Continue?"
    no_runs = "No runs to modify."
    def set_labels(selected):
        for run in selected:
            run.write_attr("label", args.label)
        cli.out("Labeled %i run(s)" % len(selected))
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        set_labels, LATEST_RUN_ARG, True)

def stop_runs(args, ctx):
    if args.remote:
        remote_impl_support.stop_runs(args)
    else:
        _stop_runs(args, ctx)

def _stop_runs(args, ctx):
    preview = "WARNING: You are about to stop the following runs:"
    confirm = "Stop {count} run(s)?"
    no_runs_help = "Nothing to stop."
    args.running = True
    def stop_f(selected):
        for run in selected:
            _stop_run(run, args.no_wait)
    def select_runs_f(args, ctx, default_runs_arg, force_deleted):
        runs = _runs_op_selected(args, ctx, default_runs_arg, force_deleted)
        return [run for run in runs if not run.remote]
    _runs_op(
        args, ctx, False, preview, confirm, no_runs_help, stop_f,
        None, False, select_runs_f)

def _stop_run(run, no_wait):
    remote_lock = remote_run_support.lock_for_run(run)
    if remote_lock:
        _try_stop_remote_run(run, remote_lock, no_wait)
    else:
        _try_stop_local_run(run)

def _try_stop_remote_run(run, remote_lock, no_wait):
    try:
        plugin = guild.plugin.for_name(remote_lock.plugin_name)
    except LookupError:
        log.warning(
            "error syncing run '%s': plugin '%s' not available",
            run.id, remote_lock.plugin_name)
    else:
        cli.out("Stopping %s (remote)" % run.id)
        plugin.stop_run(run, dict(no_wait=no_wait))

def _try_stop_local_run(run):
    pid = run.pid
    if pid and util.pid_exists(pid):
        cli.out("Stopping %s (pid %i)" % (run.id, run.pid))
        os.kill(pid, signal.SIGTERM)

def export(args, ctx):
    preview = (
        "You are about to %s the following runs to '%s':" %
        (args.move and "move" or "copy", args.location))
    confirm = "Continue?"
    no_runs = "No runs to export."
    def export(selected):
        if args.copy_resources and not args.yes:
            cli.out(
                "WARNING: you have specified --copy-resources, which will "
                "copy resources used by each run!"
                "")
            if not cli.confirm("Really copy resources exported runs?"):
                return
        util.ensure_dir(args.location)
        util.touch(os.path.join(args.location, ".guild-nocopy"))
        exported = 0
        for run in selected:
            dest = os.path.join(args.location, run.id)
            if os.path.exists(dest):
                log.warning("%s exists, skipping", dest)
                continue
            if args.move:
                cli.out("Moving {}".format(run.id))
                if args.copy_resources:
                    shutil.copytree(run.path, dest)
                    shutil.rmtree(run.path)
                else:
                    shutil.move(run.path, dest)
            else:
                cli.out("Copying {}".format(run.id))
                symlinks = not args.copy_resources
                shutil.copytree(run.path, dest, symlinks)
            exported += 1
        cli.out("Exported %i run(s)" % exported)
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        export, ALL_RUNS_ARG, True)

def import_(args, ctx):
    if not os.path.isdir(args.archive):
        cli.error("directory '{}' does not exist".format(args.archive))
    preview = (
        "You are about to import (%s) the following runs from '%s':" %
        (args.move and "move" or "copy", args.archive))
    confirm = "Continue?"
    no_runs = "No runs to import."
    def export(selected):
        if args.copy_resources and not args.yes:
            cli.out(
                "WARNING: you have specified --copy-resources, which will "
                "copy resources used by each run!"
                "")
            if not cli.confirm("Really copy resources exported runs?"):
                return
        imported = 0
        for run in selected:
            dest = os.path.join(var.runs_dir(), run.id)
            if os.path.exists(dest):
                log.warning("%s exists, skipping", run.id)
                continue
            if args.move:
                cli.out("Moving {}".format(run.id))
                if args.copy_resources:
                    shutil.copytree(run.path, dest)
                    shutil.rmtree(run.path)
                else:
                    shutil.move(run.path, dest)
            else:
                cli.out("Copying {}".format(run.id))
                symlinks = not args.copy_resources
                shutil.copytree(run.path, dest, symlinks)
            imported += 1
        cli.out("Imported %i run(s)" % imported)
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        export, ALL_RUNS_ARG, True)

def push(args, ctx):
    remote = remote_support.remote_for_args(args)
    preview = (
        "You are about to copy (push%s) the following runs to %s:" %
        (_delete_clause(args), remote.name))
    confirm = "Continue?"
    no_runs = "No runs to copy."
    def push_f(runs):
        remote_impl_support.push_runs(remote, runs, args)
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        push_f, ALL_RUNS_ARG, True)

def _delete_clause(args):
    if args.delete:
        return " with delete"
    else:
        return ""

def pull(args, ctx):
    remote = remote_support.remote_for_args(args)
    preview = (
        "You are about to copy (pull%s) the following runs from %s:"
        % (_delete_clause(args), remote.name))
    confirm = "Continue?"
    no_runs = "No runs to copy."
    def pull_f(runs):
        remote_impl_support.pull_runs(remote, runs, args)
    def filtered_runs_f(args, _ctx, _default_runs_arg, _force_deleted):
        filtered = remote_impl_support.filtered_runs_for_pull(remote, args)
        return select_runs(filtered, args.runs, ctx)
    _runs_op(
        args, ctx, False, preview, confirm,
        no_runs, pull_f, ALL_RUNS_ARG, True,
        filtered_runs_f)

def mark(args, ctx):
    if args.clear:
        _clear_marked(args, ctx)
    else:
        _mark(args, ctx)

def _clear_marked(args, ctx):
    preview = "You are about to unmark the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to modify."
    def clear(selected):
        for run in selected:
            run.del_attr("marked")
        cli.out("Unmarked %i run(s)" % len(selected))
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        clear, LATEST_RUN_ARG, True)

def _mark(args, ctx):
    preview = "You are about to mark the following runs:"
    confirm = "Continue?"
    no_runs = "No runs to modify."
    def mark(selected):
        for run in selected:
            run.write_attr("marked", True)
        cli.out("Marked %i run(s)" % len(selected))
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        mark, LATEST_RUN_ARG, True)

def publish(args, ctx):
    if args.files and args.all_files:
        cli.error("--files and --all-files cannot both be used")
    if args.refresh_index:
        _refresh_publish_index(args)
    else:
        _publish(args, ctx)
    _report_dir_size(args)

def _publish(args, ctx):
    preview = (
        "You are about to publish the following run(s) to %s:"
        % (args.dest or publishlib.DEFAULT_DEST_HOME))
    confirm = "Continue?"
    no_runs = "No runs to publish."
    def publish_f(runs, formatted):
        _publish_runs(runs, formatted, args)
        _refresh_publish_index(args, no_dest=True)
    def select_runs_f(args, ctx, default_runs_arg, force_deleted):
        runs = _runs_op_selected(args, ctx, default_runs_arg, force_deleted)
        return [
            run for run in runs
            if args.include_batch or not batch_util.is_batch(run)
        ]
    _runs_op(
        args, ctx, False, preview, confirm, no_runs,
        publish_f, ALL_RUNS_ARG, True, select_runs_f)

def _publish_runs(runs, formatted, args):
    if args.all_files:
        copy_files = publishlib.COPY_ALL_FILES
    elif args.files or args.include_links:
        copy_files = publishlib.COPY_DEFAULT_FILES
    else:
        copy_files = None
    for run, frun in zip(runs, formatted):
        cli.out("Publishing [%s] %s... " % (
            frun["short_id"],
            frun["operation"]), nl=False)
        frun["_run"] = run
        try:
            publishlib.publish_run(
                run,
                dest=args.dest,
                template=args.template,
                copy_files=copy_files,
                include_links=args.include_links,
                md5s=not args.no_md5,
                formatted_run=frun)
        except publishlib.PublishError as e:
            cli.error(
                "error publishing run %s:\n%s"
                % (run.id, e))
        else:
            dest = args.dest or publishlib.DEFAULT_DEST_HOME
            size = util.dir_size(os.path.join(dest, run.id))
            cli.out("using %s" % util.format_bytes(size))

def _refresh_publish_index(args, no_dest=False):
    if no_dest:
        dest_suffix = ""
    else:
        dest_suffix = " in %s" % (args.dest or publishlib.DEFAULT_DEST_HOME)
    print("Refreshing runs index%s" % dest_suffix)
    publishlib.refresh_index(args.dest)

def _report_dir_size(args):
    dest = args.dest or publishlib.DEFAULT_DEST_HOME
    size = util.dir_size(dest)
    cli.out("Published runs using %s" % util.format_bytes(size))
