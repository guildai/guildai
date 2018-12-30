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
import subprocess
import sys

from guild import cli

from . import runs_impl

log = logging.getLogger("guild")

def main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n"
            "Try 'guild open --help' for more information.")
    run = runs_impl.one_run(args, ctx)
    _open(run, args)
    _flush_streams_and_exit()

def _open(run, args):
    to_open = _path(run, args)
    open_f = _open_f(args)
    try:
        open_f(to_open)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("opening %s", to_open)
        cli.error(e)

def _path(run, args):
    if args.source:
        base_path = run.guild_path("source")
    else:
        base_path = run.path
    return os.path.join(base_path, args.path or "")

def _open_f(args):
    if args.cmd:
        return _subproc(args.cmd)
    elif os.name == "nt":
        return os.startfile
    elif sys.platform.startswith("darwin"):
        return _subproc("open")
    elif os.name == "posix":
        return _subproc("xdg-open")
    else:
        cli.error(
            "unsupported platform: %s %s\n"
            "Try --cmd to explicitly provide a command or "
            "'guild open --help' for more information."
            % (sys.platform, os.name))

def _subproc(prog):
    def f(path):
        subprocess.Popen([prog, path])
    return f

def _flush_streams_and_exit():
    sys.stdout.flush()
    sys.exit(0)
