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
import shlex
import subprocess
import sys

from guild import cli
from guild import cmd_impl_support
from guild import util

from . import runs_impl

log = logging.getLogger("guild")


def main(args, ctx):
    _check_args(args, ctx)
    run = runs_impl.one_run(args, ctx)
    _open(run, args)
    _flush_streams_and_exit()


def _check_args(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n" "Try 'guild open --help' for more information."
        )
    cmd_impl_support.check_incompatible_args(
        [
            ("shell", "cmd"),
            ("shell_cmd", "shell"),
            ("shell_cmd", "cmd"),
        ],
        args,
        ctx,
    )


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
    if args.output:
        _check_non_output_args(args)
        return run.guild_path("output")
    return os.path.join(_path_root(args, run), args.path or "")


def _check_non_output_args(args):
    if args.path or args.sourcecode:
        cli.out(
            "--output cannot be used with other options - " "ignorning other options",
            err=True,
        )


def _path_root(args, run):
    if args.sourcecode:
        return run.guild_path("sourcecode")
    else:
        return run.path


def _open_f(args):
    if args.cmd:
        return _subproc_f(args.cmd)
    elif args.shell or args.shell_cmd:
        return _shell_f(args.shell_cmd)
    elif os.name == "nt":
        return os.startfile
    elif sys.platform.startswith("darwin"):
        return _subproc_f("open")
    elif os.name == "posix":
        return _subproc_f("xdg-open")
    else:
        cli.error(
            "unsupported platform: %s %s\n"
            "Try --cmd to explicitly provide a command or "
            "'guild open --help' for more information." % (sys.platform, os.name)
        )


def _subproc_f(prog):
    cmd = shlex.split(prog)

    def f(path):
        p = subprocess.Popen(cmd + [path])
        p.wait()

    return f


def _flush_streams_and_exit():
    sys.stdout.flush()
    sys.exit(0)


def _shell_f(shell_cmd):
    try:
        import pty
    except ImportError:
        cli.error("shell is not supported on this platform (%s)" % util.PLATFORM)

    shell_cmd = shell_cmd or os.getenv("SHELL", "bash")

    def f(path):
        if os.path.isfile(path):
            path = os.path.dirname(path)
        cli.note(
            "Running a new shell in %s\n"
            "To exit the shell, type 'exit' and press Enter." % path
        )
        with util.Chdir(path):
            with _fix_shell_columns():
                pty.spawn([shell_cmd])

    return f


def _fix_shell_columns():
    # pty seems to use COLUMNS=80 by default so we define here
    # to work around wrapping wrapping issues.
    return util.Env({"COLUMNS": str(cli.MAX_WIDTH)})
