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
import re
import subprocess

import six

from guild import cli
from guild import click_util
from guild import config
from guild import run_util
from guild import util

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")

DEFAULT_DIFF_CMD = "diff -ru"


class OneRunArgs(click_util.Args):
    def __init__(self, base_args, run):
        kw = base_args.as_kw()
        kw.pop("runs")
        kw["run"] = run
        super(OneRunArgs, self).__init__(**kw)


def main(args, ctx):
    if args.remote:
        remote_impl_support.diff_runs(args)
    else:
        _main(args, ctx)


def _main(args, ctx):
    _validate_args(args)
    _apply_default_runs(args)
    if args.working or args.working_dir:
        _diff_working(args, ctx)
    else:
        _diff_runs(args, ctx)


def _validate_args(args):
    if args.working and args.working_dir:
        cli.error("--working and --working-dir cannot both be specified")


def _apply_default_runs(args):
    if len(args.runs) == 0:
        if args.working or args.working_dir:
            args.runs = ("1", None)
        else:
            args.runs = ("2", "1")
    elif len(args.runs) == 1:
        if args.working or args.working_dir:
            args.runs = (args.runs[0], None)
        else:
            cli.error(
                "diff requires two runs\n"
                "Try specifying a second run or 'guild diff --help' "
                "for more information."
            )
    elif len(args.runs) > 2:
        cli.error(
            "cannot compare more than two runs\n"
            "Try specifying just two runs or 'guild diff --help' for "
            "more information."
        )
    else:
        assert len(args.runs) == 2, args
        if args.working:
            cli.error("cannot specify RUN2 and --working")
        if args.working_dir:
            cli.error("cannot specify RUN2 and --working-dir")


def _diff_working(args, ctx):
    assert len(args.runs) == 2, args
    assert args.runs[0] is not None and args.runs[1] is None, args
    run = runs_impl.one_run(OneRunArgs(args, args.runs[0]), ctx)
    run_sourcecode_dir = run.guild_path("sourcecode")
    if args.working_dir:
        working_dir = os.path.join(config.cwd(), args.working_dir)
    else:
        assert args.working
        working_dir = _find_run_working_dir(run)
    if not args.path:
        _diff(
            run_sourcecode_dir,
            working_dir,
            args,
        )
    else:
        for path in args.path:
            _diff(
                os.path.join(run_sourcecode_dir, path),
                os.path.join(working_dir, path),
                args,
            )


def _find_run_working_dir(run):
    working_dir = util.find_apply([_opdef_sourcecode_root, _script_source], run)
    if not working_dir:
        cli.error(
            "cannot find working source code directory for run {run_id}\n"
            "Try specifying the directory with 'guild diff {run_id} "
            "--working-dir DIR'.".format(run_id=run.short_id)
        )
    return working_dir


def _opdef_sourcecode_root(run):
    opdef = run_util.run_opdef(run)
    if opdef:
        return os.path.join(opdef.guildfile.dir, opdef.sourcecode.root or "")
    return None


def _script_source(run):
    if run.opref.pkg_type == "script":
        return run.opref.pkg_name
    return None


def _diff_runs(args, ctx):
    assert len(args.runs) == 2, args
    assert args.runs[0] is not None and args.runs[1] is not None, args
    run1 = runs_impl.one_run(OneRunArgs(args, args.runs[0]), ctx)
    run2 = runs_impl.one_run(OneRunArgs(args, args.runs[1]), ctx)
    for path in _diff_paths(args):
        _diff(os.path.join(run1.dir, path), os.path.join(run2.dir, path), args)


def _diff(path1, path2, args):
    cmd_base = util.shlex_split(_diff_cmd(args, path1))
    cmd = cmd_base + [path1, path2]
    log.debug("diff cmd: %r", cmd)
    try:
        subprocess.call(cmd)
    except OSError as e:
        cli.error("error running '%s': %s" % (" ".join(cmd), e))


def _diff_cmd(args, path1):
    return args.cmd or _config_diff_cmd(path1) or _default_diff_cmd(path1)


def _config_diff_cmd(path1):
    cmd_map = _coerce_config_diff_command(_diff_command_config())
    if not cmd_map:
        return None
    if not path1:
        return cmd_map.get("default")
    return _config_diff_cmd_for_path(path1, cmd_map)


def _diff_command_config():
    return config.user_config().get("diff", {}).get("command")


def _config_diff_cmd_for_path(path1, cmd_map):
    _, path_ext = os.path.splitext(path1)
    for pattern in cmd_map:
        if pattern == "default":
            continue
        if _match_ext(path_ext, pattern):
            return cmd_map[pattern]
    return cmd_map.get("default")


def _match_ext(ext, pattern):
    return ext == pattern or _safe_re_match(ext, pattern)


def _safe_re_match(ext, pattern):
    try:
        p = re.compile(pattern)
    except ValueError:
        return False
    else:
        return p.search(ext)


def _coerce_config_diff_command(data):
    if data is None or isinstance(data, dict):
        return data
    elif isinstance(data, six.string_types):
        return {"default": data}
    else:
        log.warning("unsupported configuration for diff command: %r", data)
        return None


def _default_diff_cmd(path1):
    return _default_diff_cmd_for_path(path1) or _default_diff_cmd_()


def _default_diff_cmd_for_path(path1):
    if not path1:
        return None
    _, ext = os.path.splitext(path1)
    if ext == ".ipynb":
        return _find_cmd(["nbdiff-web -M"])


def _default_diff_cmd_():
    if util.PLATFORM == "Linux":
        return _find_cmd(["meld", "xxdiff -r", "dirdiff", "colordiff"])
    elif util.PLATFORM == "Darwin":
        return _find_cmd(["Kaleidoscope", "meld", "DiffMerge", "FileMerge"])
    else:
        return DEFAULT_DIFF_CMD


def _find_cmd(cmds):
    for cmd in cmds:
        if util.which(cmd.split(" ", 1)[0]):
            return cmd
    return DEFAULT_DIFF_CMD


def _diff_paths(args):
    paths = []
    if args.attrs:
        paths.append(os.path.join(".guild", "attrs"))
        if args.env:
            log.warning("ignoring --env (already included in --attrs)")
        if args.flags:
            log.warning("ignoring --flags (already included in --attrs)")
        if args.deps:
            log.warning("ignoring --deps (already included in --attrs)")
    else:
        if args.env:
            paths.append(os.path.join(".guild", "attrs", "env"))
        if args.flags:
            paths.append(os.path.join(".guild", "attrs", "flags"))
        if args.deps:
            paths.append(os.path.join(".guild", "attrs", "deps"))
    if args.output:
        paths.append(os.path.join(".guild", "output"))
    if args.sourcecode:
        if args.path:
            paths.extend(
                [os.path.join(".guild", "sourcecode", path) for path in args.path]
            )
        else:
            paths.append(os.path.join(".guild", "sourcecode"))
    else:
        paths.extend(args.path)
    if not paths:
        paths.append("")
    return paths
