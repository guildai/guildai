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
import os
import re

import six
import yaml

from guild import util

log = logging.getLogger("guild")

MIN_MONITOR_INTERVAL = 5

MAX_LABEL_LEN = 60

class RunsMonitor(util.LoopingThread):

    STOP_TIMEOUT = 5

    def __init__(self, list_runs_cb, logdir, interval):
        """Create a RunsMonitor.

        Note that run links are created initially by this
        function. Any errors result from user input will propagate
        during this call. Similar errors occuring after the monitor is
        started will be logged but will not propagate.
        """
        interval = min(interval, MIN_MONITOR_INTERVAL)
        super(RunsMonitor, self).__init__(
            cb=self.run_once,
            interval=interval,
            stop_timeout=self.STOP_TIMEOUT)
        self.logdir = logdir
        self.list_runs_cb = list_runs_cb
        self.run_once(exit_on_error=True)

    def run_once(self, exit_on_error=False):
        log.debug("Refreshing runs")
        try:
            runs = self.list_runs_cb()
        except SystemExit as e:
            if exit_on_error:
                raise
            log.error(
                "An error occurred while reading runs. "
                "Use --debug for details.")
            log.debug(e)
        else:
            self._refresh_run_links(runs)

    def _refresh_run_links(self, runs):
        # List of links to delete - assume all to start
        to_delete = os.listdir(self.logdir)
        for run in runs:
            link_name = self._format_run_name(run)
            util.apply_remove(link_name, to_delete)
            link_path = os.path.join(self.logdir, link_name)
            if not os.path.exists(link_path):
                self._create_run_link(link_path, run.path)
            self._refresh_run_link(link_path, run.path)
        for link_name in to_delete:
            self._remove_run_link(os.path.join(self.logdir, link_name))

    @staticmethod
    def _format_run_name(run):
        parts = [run.short_id]
        if run.opref.model_name:
            parts.append("%s:%s" % (run.opref.model_name, run.opref.op_name))
        else:
            parts.append(run.opref.op_name)
        parts.append(util.format_timestamp(run.get("started")))
        label = run.get("label")
        if label:
            parts.append(label)
        return util.safe_filename(" ".join(parts))

    @staticmethod
    def _create_run_link(link, run_dir):
        log.debug("Linking %s to %s", link, run_dir)
        util.symlink(run_dir, link)

    def _refresh_run_link(self, link, run_dir):
        """Callback to let subclass refresh links they may have created."""
        pass

    @staticmethod
    def _remove_run_link(link):
        log.debug("Removing %s", link)
        os.remove(link)

def format_run(run, index=None):
    status = run.status
    operation = format_op_desc(run)
    marked = bool(run.get("marked"))
    started = run.get("started")
    stopped = run.get("stopped")
    return {
        "_run": run,
        "id": run.id,
        "short_id": run.short_id,
        "index": _format_run_index(run, index),
        "short_index": _format_run_index(run),
        "model": run.opref.model_name,
        "op_name": run.opref.op_name,
        "operation": operation,
        "operation_with_marked": _op_with_marked(operation, marked),
        "pkg": run.opref.pkg_name,
        "status": status,
        "status_with_remote": _status_with_remote(status, run.remote),
        "marked": _format_val(marked),
        "label": _format_label(run.get("label") or ""),
        "pid": run.pid or "",
        "started": util.format_timestamp(started),
        "stopped": util.format_timestamp(stopped),
        "duration": util.format_duration(started, stopped),
        "run_dir": util.format_dir(run.path),
        "command": _format_command(run.get("cmd", "")),
        "exit_status": _format_exit_status(run)
    }

def _format_run_index(run, index=None):
    if index is not None:
        return "[%i:%s]" % (index, run.short_id)
    else:
        return "[%s]" % run.short_id

def _op_with_marked(operation, marked):
    if marked:
        return operation + " [marked]"
    return operation

def _status_with_remote(status, remote):
    if remote:
        return "{} ({})".format(status, remote)
    else:
        return status

def _format_label(label):
    if len(label) > MAX_LABEL_LEN:
        label = label[:MAX_LABEL_LEN] + u"\u2026"
    return label

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

def format_op_desc(run, nowarn=False, seen_protos=None):
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
                opref.pkg_type, opref.pkg_name)
        return "?"

def _format_guildfile_op(opref):
    parts = []
    gf_dir = _guildfile_dir(opref)
    if gf_dir:
        parts.extend([gf_dir, os.path.sep])
    if opref.model_name:
        parts.extend([opref.model_name, ":"])
    parts.append(opref.op_name)
    return "".join(parts)

def _guildfile_dir(opref):
    from guild import config
    gf_dir = os.path.dirname(opref.pkg_name)
    real_cwd = config.cwd()
    relpath = os.path.relpath(gf_dir, real_cwd)
    if relpath == ".":
        return ""
    return re.sub(r"\.\./(\.\./)+", ".../", _ensure_dot_path(relpath))

def _ensure_dot_path(path):
    if path[0:1] == ".":
        return path
    return os.path.join(".", path)

def _format_package_op(opref):
    return "%s/%s:%s" % (opref.pkg_name, opref.model_name, opref.op_name)

def _format_script_op(opref):
    return _format_guildfile_op(opref)

def _format_builtin_op(opref):
    return opref.op_name

def _format_pending_op(opref):
    return "<pending %s>" % opref.op_name

def _format_test_op(opref):
    return "%s:%s" % (opref.model_name, opref.op_name)

def _format_func_op(opref):
    return "%s()" % opref.op_name

def _apply_batch_desc(base_desc, run, seen_protos):
    import guild.run
    try:
        proto_dir = run.guild_path("proto")
    except TypeError:
        # Occurs for run proxies that don't support guild_path - punt
        # with generic descriptor. (TODO: implement explicit behavior
        # in run interface + proxy)
        proto_dir = ""
    if not os.path.exists(proto_dir):
        return base_desc
    if proto_dir in seen_protos:
        # We have a cycle - drop this proto_dir
        return base_desc
    proto_run = guild.run.Run("", proto_dir)
    proto_op_desc = format_op_desc(proto_run, seen_protos)
    parts = [proto_op_desc]
    if not base_desc.startswith("+"):
        parts.append("+")
    parts.append(base_desc)
    return "".join(parts)

def _format_val(val):
    if val is None:
        return ""
    elif val is True:
        return "yes"
    elif val is False:
        return "no"
    elif isinstance(val, (int, float, six.string_types)):
        return str(val)
    else:
        return _format_yaml_block(val)

def _format_yaml_block(val):
    formatted = yaml.dump(val, default_flow_style=False)
    lines = formatted.split("\n")
    padded = ["  " + line for line in lines]
    return "\n" + "\n".join(padded).rstrip()

def format_flag_val(val):
    if val is True:
        return "yes"
    elif val is False:
        return "no"
    elif val is None:
        return "null"
    elif isinstance(val, list):
        return _format_flag_list(val)
    elif isinstance(val, (six.string_types, float)):
        return _yaml_format(val)
    else:
        return str(val)

def _format_flag_list(val_list):
    joined = ", ".join([format_flag_val(val) for val in val_list])
    return "[%s]" % joined

def _yaml_format(val):
    formatted = yaml.safe_dump(val).strip()
    if formatted.endswith("\n..."):
        formatted = formatted[:-4]
    return formatted

def format_attr(val):
    if isinstance(val, list):
        return _format_attr_list(val)
    elif isinstance(val, dict):
        return _format_attr_dict(val)
    else:
        return _format_val(val)

def _format_attr_list(l):
    return "\n%s" % "\n".join([
        "  %s" % _format_val(item) for item in l
    ])

def _format_attr_dict(d):
    return "\n%s" % "\n".join([
        "  %s: %s" % (key, _format_val(d[key]))
        for key in sorted(d)
    ])

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
