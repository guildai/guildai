# Copyright 2017-2022 RStudio, PBC
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

import logging
import os
import re
import subprocess

import six

from guild import cli
from guild import click_util
from guild import cmd_impl_support
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
        kw['run'] = run
        super().__init__(**kw)


def main(args, ctx):
    if args.remote:
        remote_impl_support.diff_runs(args)
    else:
        _main(args, ctx)


def _main(args, ctx):
    _validate_args(args, ctx)
    _apply_default_runs(args)
    if args.dir:
        _diff_dir(args, ctx)
    elif args.working:
        _diff_working(args, ctx)
    else:
        _diff_runs(args, ctx)


def _validate_args(args, ctx):
    incompatible = [
        ("working", "dir"),
        ("working", "sourcecode"),
    ]
    cmd_impl_support.check_incompatible_args(incompatible, args, ctx)


def _apply_default_runs(args):
    if not args.run:
        if args.dir or args.working:
            args.run = "1"
        else:
            args.run, args.other_run = ("2", "1")
    elif not args.other_run:
        if args.dir or args.working:
            args.run, args.other_run = (args.run, None)
        else:
            cli.error(
                "diff requires two runs\n"
                "Try specifying a second RUN or 'guild diff --help' "
                "for more information."
            )
    else:
        assert args.other_run, args
        if args.dir:
            cli.error("cannot specify second RUN and --dir")
        if args.working:
            cli.error("cannot specify second RUN and --working")


def _diff_dir(args, ctx):
    run = _one_run_for_args(args, ctx)
    _diff_dirs(run.dir, args.dir, args)


def _one_run_for_args(args, ctx):
    return runs_impl.one_run(OneRunArgs(args, args.run), ctx)


def _diff_dirs(dir, other_dir, args):
    if args.paths:
        for path in args.paths:
            _diff(os.path.join(dir, path), os.path.join(other_dir, path), args)
    else:
        _diff(dir, other_dir, args)


def _diff_working(args, ctx):
    run = _one_run_for_args(args, ctx)
    run_sourcecode_dir = run_util.sourcecode_dir(run)
    working_dir = _working_dir(run, args)
    _diff_dirs(run_sourcecode_dir, working_dir, args)


def _working_dir(run, args):
    if args.dir:
        return os.path.join(config.cwd(), args.dir)
    assert args.working
    return _working_dir_for_run(run)


def _working_dir_for_run(run):
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
    assert args.run and args.other_run, args
    run = runs_impl.one_run(OneRunArgs(args, args.run), ctx)
    other_run = runs_impl.one_run(OneRunArgs(args, args.other_run), ctx)
    for path, other_path in _diff_paths(run, other_run, args):
        _diff(path, other_path, args)


def _diff(path, other_path, args):
    cmd_base = util.shlex_split(_diff_cmd(args, path))
    cmd = cmd_base + [path, other_path]
    log.debug("diff cmd: %r", cmd)
    try:
        subprocess.call(cmd)
    except OSError as e:
        cli.error(f"error running '{' '.join(cmd)}': {e}")


def _diff_cmd(args, path):
    return args.cmd or _config_diff_cmd(path) or _default_diff_cmd(path)


def _config_diff_cmd(path):
    cmd_map = _coerce_config_diff_command(_diff_command_config())
    if not cmd_map:
        return None
    if not path:
        return cmd_map.get("default")
    return _config_diff_cmd_for_path(path, cmd_map)


def _diff_command_config():
    return config.user_config().get("diff", {}).get("command")


def _config_diff_cmd_for_path(path, cmd_map):
    _root, path_ext = os.path.splitext(path)
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
    if isinstance(data, six.string_types):
        return {"default": data}
    log.warning("unsupported configuration for diff command: %r", data)
    return None


def _default_diff_cmd(path):
    return _default_diff_cmd_for_path(path) or _default_diff_cmd_()


def _default_diff_cmd_for_path(path):
    if not path:
        return None
    _root, ext = os.path.splitext(path)
    if ext == ".ipynb":
        return _find_cmd(["nbdiff-web -M"])
    return None


def _default_diff_cmd_():
    if util.get_platform() == "Linux":
        return _find_cmd(["meld", "xxdiff -r", "dirdiff", "colordiff"])
    if util.get_platform() == "Darwin":
        return _find_cmd(["Kaleidoscope", "meld", "DiffMerge", "FileMerge"])
    return DEFAULT_DIFF_CMD


def _find_cmd(cmds):
    for cmd in cmds:
        if util.which(cmd.split(" ", 1)[0]):
            return cmd
    return DEFAULT_DIFF_CMD


def _diff_paths(run, other_run, args):
    paths = []
    if args.attrs:
        _warn_redundant_attr_options(args)
        paths.extend(_attrs_paths(run, other_run))
    else:
        if args.env:
            paths.extend(_env_paths(run, other_run))
        if args.flags:
            paths.extend(_flags_paths(run, other_run))
        if args.deps:
            paths.extend(_deps_paths(run, other_run))
    if args.output:
        paths.extend(_output_paths(run, other_run))
    if args.sourcecode:
        paths.extend(_sourcecode_paths(run, other_run, args))
    else:
        paths.extend(_base_paths(run, other_run, args))
    if not paths:
        paths.append((run.dir, other_run.dir))
    return paths


def _warn_redundant_attr_options(args):
    if args.env:
        log.warning("ignoring --env (already included in --attrs)")
    if args.flags:
        log.warning("ignoring --flags (already included in --attrs)")
    if args.deps:
        log.warning("ignoring --deps (already included in --attrs)")


def _attrs_paths(run, other_run):
    return [(run.guild_path("attrs"), other_run.guild_path("attrs"))]


def _env_paths(run, other_run):
    return [(run.guild_path("attrs", "env"), other_run.guild_path("attrs", "env"))]


def _flags_paths(run, other_run):
    return [(run.guild_path("attrs", "flags"), other_run.guild_path("attrs", "flags"))]


def _deps_paths(run, other_run):
    return [(run.guild_path("attrs", "deps"), other_run.guild_path("attrs", "deps"))]


def _output_paths(run, other_run):
    return [(run.guild_path("output"), other_run.guild_path("output"))]


def _sourcecode_paths(run, other_run, args):
    run_sourcecode_dir = run_util.sourcecode_dir(run)
    other_run_sourcecode_dir = run_util.sourcecode_dir(other_run)
    if args.paths:
        return [
            (
                os.path.join(run_sourcecode_dir, path),
                os.path.join(other_run_sourcecode_dir, path),
            )
            for path in args.paths
        ]
    return [(run_sourcecode_dir, other_run_sourcecode_dir)]


def _base_paths(run, other_run, args):
    return [
        (os.path.join(run.dir, path), os.path.join(other_run.dir, path))
        for path in args.paths
    ]
