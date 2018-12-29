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
import shlex
import subprocess

from guild import cli
from guild import click_util
from guild import config

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
    if len(args.runs) == 0:
        args.runs = ("2", "1")
    elif len(args.runs) == 1:
        cli.error(
            "diff requires two runs\n"
            "Try specifying a second run or 'guild diff --help' "
            "for more information.")
    elif len(args.runs) > 2:
        cli.error(
            "cannot compare more than two runs\n"
            "Try specifying just two runs or 'guild diff --help' for "
            "more information.")
    assert len(args.runs) == 2, args
    run1 = runs_impl.one_run(OneRunArgs(args, args.runs[0]), ctx)
    run2 = runs_impl.one_run(OneRunArgs(args, args.runs[1]), ctx)
    _diff(run1, run2, args)

def _diff(run1, run2, args):
    cmd_base = shlex.split(_diff_cmd(args))
    for path in _diff_paths(args):
        dir1 = os.path.join(run1.path, path)
        dir2 = os.path.join(run2.path, path)
        cmd = cmd_base + [dir1, dir2]
        log.debug("diff cmd: %r", cmd)
        subprocess.call(cmd)

def _diff_cmd(args):
    return args.cmd or _config_diff_cmd() or DEFAULT_DIFF_CMD

def _config_diff_cmd():
    return config.user_config().get("diff", {}).get("command")

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
    if args.source:
        paths.append(os.path.join(".guild", "source"))
    paths.extend(args.path)
    if not paths:
        paths.append("")
    return paths
