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

import logging
import os

import six
import yaml

from guild import flag_util
from guild import guildfile
from guild import opref as opreflib
from guild import resolver
from guild import run as runlib
from guild import util

log = logging.getLogger("guild")

DEFAULT_MONITOR_INTERVAL = 5
MIN_MONITOR_INTERVAL = 5
MAX_RUN_NAME_LEN = 242


class RunsMonitor(util.LoopingThread):

    STOP_TIMEOUT = 5

    def __init__(
        self, logdir, list_runs_cb, refresh_run_cb, interval=None, run_name_cb=None
    ):
        """Create a RunsMonitor.

        Note that run links are created initially by this
        function. Any errors result from user input will propagate
        during this call. Similar errors occuring after the monitor is
        started will be logged but will not propagate.
        """
        interval = interval or DEFAULT_MONITOR_INTERVAL
        if interval < MIN_MONITOR_INTERVAL:
            raise ValueError(
                "interval %r is too low - must be at least %i"
                % (interval, MIN_MONITOR_INTERVAL)
            )
        super(RunsMonitor, self).__init__(
            cb=self.run_once, interval=interval, stop_timeout=self.STOP_TIMEOUT
        )
        self.logdir = logdir
        self.list_runs_cb = list_runs_cb
        self.refresh_run_cb = refresh_run_cb
        self.run_name_cb = run_name_cb or default_run_name

    def run_once(self, exit_on_error=False):
        log.debug("Refreshing runs")
        try:
            runs = self.list_runs_cb()
        except SystemExit as e:
            if exit_on_error:
                raise
            log.error(
                "An error occurred while reading runs. " "Use --debug for details."
            )
            log.debug(e)
        else:
            self._refresh_logdir(runs)

    def _refresh_logdir(self, runs):
        to_delete = self._run_dirs()
        for run in runs:
            name = self.run_name_cb(run)
            util.safe_list_remove(name, to_delete)
            path = self._ensure_run(name)
            self.refresh_run_cb(run, path)
        for name in to_delete:
            self._delete_run(name)

    def _run_dirs(self):
        return [
            name
            for name in os.listdir(self.logdir)
            if os.path.isdir(os.path.join(self.logdir, name))
        ]

    def _ensure_run(self, name):
        safe_name = util.safe_filename(name)
        path = os.path.join(self.logdir, safe_name)
        _ensure_dir(path)
        return path

    def _delete_run(self, name):
        path = os.path.join(self.logdir, name)
        util.safe_rmtree(path)


def _ensure_dir(path):
    util.ensure_dir(_safe_len_path(path))


def _safe_len_path(p):
    if util.PLATFORM == "Windows":
        # See http://bit.ly/windows-long-file-names
        return "\\\\?\\" + p
    return p


def default_run_name(run):
    return run_name(run, run.get("label"))


def run_name(run, label):
    parts = [run.short_id]
    if run.opref.model_name:
        parts.append("%s:%s" % (run.opref.model_name, run.opref.op_name))
    else:
        parts.append(run.opref.op_name)
    parts.append(util.format_timestamp(run.get("started")))
    if label:
        parts.append(label)
    return util.safe_filename(" ".join(parts))[:MAX_RUN_NAME_LEN]


def format_run(run, index=None):
    status = run.status
    started = run.get("started")
    stopped = run.get("stopped")
    return {
        "_run": run,
        "command": _format_command(run.get("cmd", "")),
        "duration": util.format_duration(started, stopped),
        "exit_status": _format_exit_status(run),
        "from": format_pkg_name(run),
        "id": run.id,
        "index": _format_run_index(run, index),
        "label": run.get("label") or "",
        "marked": format_attr(bool(run.get("marked"))),
        "model": run.opref.model_name,
        "op_name": run.opref.op_name,
        "operation": format_operation(run),
        "pid": run.pid or "",
        "pkg_name": run.opref.pkg_name,
        "run_dir": util.format_dir(run.path),
        "short_id": run.short_id,
        "short_index": _format_run_index(run),
        "sourcecode_digest": run.get("sourcecode_digest", ""),
        "vcs_commit": run.get("vcs_commit", ""),
        "started": util.format_timestamp(started),
        "status": status,
        "status_with_remote": _status_with_remote(status, run.remote),
        "stopped": util.format_timestamp(stopped),
    }


def _format_run_index(run, index=None):
    if index is not None:
        return "[%i:%s]" % (index, run.short_id)
    else:
        return "[%s]" % run.short_id


def _with_marked(s, marked):
    if marked:
        return s + " [marked]"
    return s


def _status_with_remote(status, remote):
    if remote:
        return "{} ({})".format(status, remote)
    else:
        return status


def _format_command(cmd):
    if not cmd:
        return ""
    return " ".join([_maybe_quote_arg(arg) for arg in cmd])


def _maybe_quote_arg(arg):
    arg = str(arg)
    if arg == "" or " " in arg:
        return '"%s"' % arg
    else:
        return arg


def _format_exit_status(run):
    return run.get("exit_status.remote", "") or run.get("exit_status", "")


def format_pkg_name(run):
    opref = run.opref
    if opref.pkg_type == "guildfile":
        return _format_guildfile_pkg_name(opref)
    elif opref.pkg_type == "script":
        return _format_script_pkg_name(opref)
    elif opref.pkg_type == "package":
        return "%s==%s" % (opref.pkg_name, opref.pkg_version)
    else:
        return opref.pkg_name


def _format_guildfile_pkg_name(opref):
    return util.format_dir(opref.pkg_name)


def _format_script_pkg_name(opref):
    return util.format_dir(opref.pkg_name)


def format_operation(run, nowarn=False, seen_protos=None):
    seen_protos = seen_protos or set()
    opref = run.opref
    base_desc = _base_op_desc(opref, nowarn)
    return _apply_batch_desc(base_desc, run, seen_protos)


def _base_op_desc(opref, nowarn):
    if opref.pkg_type == "guildfile":
        return _format_guildfile_op(opref)
    elif opref.pkg_type == "package":
        return _format_package_op(opref)
    elif opref.pkg_type == "script":
        return _format_script_op(opref)
    elif opref.pkg_type == "builtin":
        return _format_builtin_op(opref)
    elif opref.pkg_type == "pending":
        return _format_pending_op(opref)
    elif opref.pkg_type == "test":
        return _format_test_op(opref)
    elif opref.pkg_type == "func":
        return _format_func_op(opref)
    else:
        if not nowarn:
            log.warning(
                "cannot format op desc, unexpected pkg type: %s (%s)",
                opref.pkg_type,
                opref.pkg_name,
            )
        return "?"


def _format_guildfile_op(opref):
    return _full_op_name(opref)


def _full_op_name(opref):
    if opref.model_name:
        return "".join([opref.model_name, ":", opref.op_name])
    return opref.op_name


def _format_package_op(opref):
    if not opref.model_name:
        return "%s/%s" % (opref.pkg_name, opref.op_name)
    return "%s/%s:%s" % (opref.pkg_name, opref.model_name, opref.op_name)


def _format_script_op(opref):
    return _full_op_name(opref)


def _format_builtin_op(opref):
    return opref.op_name


def _format_pending_op(opref):
    return opref.op_name


def _format_test_op(opref):
    return "%s:%s" % (opref.model_name, opref.op_name)


def _format_func_op(opref):
    return "%s()" % opref.op_name


def _apply_batch_desc(base_desc, run, seen_protos):
    proto_dir = _safe_guild_path(run, "proto", "")
    if not os.path.exists(proto_dir):
        return base_desc
    if proto_dir in seen_protos:
        # We have a cycle - drop this proto_dir
        return base_desc
    proto_run = runlib.Run("", proto_dir)
    proto_op_desc = format_operation(proto_run, seen_protos)
    parts = [proto_op_desc]
    if not base_desc.startswith("+"):
        parts.append("+")
    parts.append(base_desc)
    return "".join(parts)


def _safe_guild_path(run, path, default):
    try:
        return run.guild_path(path)
    except TypeError:
        # Occurs for run proxies that don't support guild_path - punt
        # with generic descriptor.
        return default


def shorten_op_dir(op_dir, cwd):
    return util.shorten_path(_format_op_dir(op_dir, cwd))


def _format_op_dir(op_dir, cwd):
    return util.find_apply(
        [_try_format_subpath, _try_format_peerpath, _default_format_dir], op_dir, cwd
    )


def _try_format_subpath(dir, cwd):
    try:
        return util.subpath(dir, cwd)
    except ValueError:
        return None


def _try_format_peerpath(dir, cwd):
    cwd_parent = os.path.dirname(cwd)
    if cwd_parent == dir:
        return ".." + os.path.sep
    try:
        subpath = util.subpath(dir, cwd_parent)
    except ValueError:
        return None
    else:
        return os.path.join("..", subpath)


def _default_format_dir(dir, _cwd):
    return util.format_dir(dir)


def format_attr(val):
    if val is None:
        return ""
    elif isinstance(val, six.string_types):
        return val
    elif isinstance(val, (bool, int, float)):
        return flag_util.encode_flag_val(val)
    elif isinstance(val, list):
        return _format_attr_list(val)
    elif isinstance(val, dict):
        return _format_attr_dict(val)
    else:
        return _format_yaml_block(val)


def _format_attr_list(l):
    return "\n%s" % "\n".join(["  %s" % format_attr(item) for item in l])


def _format_attr_dict(d):
    return "\n%s" % "\n".join(
        ["  %s: %s" % (key, format_attr(d[key])) for key in sorted(d)]
    )


def _format_yaml_block(val):
    formatted = yaml.dump(val, default_flow_style=False)
    lines = formatted.split("\n")
    padded = ["  " + line for line in lines]
    return "\n" + "\n".join(padded).rstrip()


def iter_output(run):
    try:
        f = open(run.guild_path("output"), "r")
    except IOError as e:
        if e.errno != 2:
            raise
    else:
        with f:
            for line in f:
                yield line


def run_scalar_key(scalar):
    if not isinstance(scalar, dict):
        return ""
    prefix = scalar.get("prefix")
    tag = scalar.get("tag")
    if not prefix or prefix == ".guild":
        return tag
    return "%s#%s" % (prefix, tag)


def latest_compare(run):
    return util.find_apply([_try_guildfile_compare, _run_compare_attr], run)


def _try_guildfile_compare(run):
    opdef = run_opdef(run)
    if opdef:
        return opdef.compare
    return None


def run_opdef(run):
    gf = run_guildfile(run)
    if gf:
        return _try_guildfile_opdef(gf, run)
    return None


def run_guildfile(run):
    try:
        return guildfile.for_run(run)
    except (guildfile.NoModels, guildfile.GuildfileMissing, TypeError):
        return None


def run_project_dir(run):
    if run.opref.pkg_type == "script":
        return run.opref.pkg_name
    else:
        gf = run_guildfile(run)
        return gf.dir if gf else None


def _try_guildfile_opdef(gf, run):
    try:
        m = gf.models[run.opref.model_name]
    except KeyError:
        return None
    else:
        return m.get_operation(run.opref.op_name)


def _run_compare_attr(run):
    return run.get("compare")


def run_for_run_dir(run_dir):
    if run_dir[:1] == ".":
        run_dir = os.path.abspath(run_dir)
    if not os.path.isabs(run_dir):
        return None
    run_id = os.path.basename(run_dir)
    return runlib.Run(run_id, run_dir)


def marked_or_latest_run_for_opspec(opspec):
    try:
        opref = opreflib.OpRef.for_string(opspec)
    except opreflib.OpRefError:
        return None
    else:
        return resolver.marked_or_latest_run([opref])
