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

import fnmatch
import logging
import os
import subprocess

from guild import cli
from guild import util

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")


def main(args, ctx):
    if args.remote:
        _check_ignored_remote_opts(args)
        remote_impl_support.list_files(args)
    else:
        _main(args, ctx)


def _check_ignored_remote_opts(args):
    if args.full_path:
        log.warning("--full-path is not supported for remote " "file lists - ignoring")


def _main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n" "Try 'guild ls --help' for more information."
        )
    run = runs_impl.one_run(args, ctx)
    _print_header(run.dir, args)
    if args.extended:
        _ls_extended(run.dir, args)
    else:
        _ls_normal(run.dir, args)


def _print_header(run_dir, args):
    if not args.full_path and not args.no_format:
        cli.out("%s:" % _run_dir_header(run_dir, args))


def _run_dir_header(run_dir, args):
    if os.getenv("NO_HEADER_PATH") == "1":
        run_dir = os.path.basename(run_dir)
    if args.sourcecode:
        return os.path.join(run_dir, ".guild/sourcecode")
    elif not args.full_path:
        return util.format_dir(run_dir)
    else:
        return run_dir


def _ls_extended(dir, args):
    path = _path_for_extended(dir, args)
    cmd = ["ls", "-l"]
    if args.all:
        cmd.append("-aR")
    if args.human_readable:
        cmd.append("-h")
    if args.follow_links:
        cmd.append("-L")
    cmd.append(path)
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        cli.error(e.output.strip())
    else:
        cli.out(out.strip())


def _path_for_extended(dir, args):
    return os.path.join(dir, _rel_path(args))


def _ls_normal(dir, args):
    for val in sorted(_list(dir, args)):
        _print_file(val, args)


def _list(run_dir, args):
    match_path_pattern = _rel_path(args)
    for root, dirs, files in os.walk(run_dir, followlinks=args.follow_links):
        _maybe_rm_guild_dir(dirs, args)
        for name in dirs + files:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, run_dir)
            if not _match_path(rel_path, match_path_pattern):
                continue
            if os.path.isdir(full_path):
                suffix = os.path.sep
            else:
                suffix = ""
            if args.full_path:
                yield full_path + suffix
            else:
                yield rel_path + suffix


def _rel_path(args):
    pattern = args.path or ""
    if args.sourcecode:
        source_base = os.path.join(".guild", "sourcecode")
        if pattern:
            pattern = os.path.join(source_base, pattern)
        else:
            pattern = source_base
    return pattern


def _maybe_rm_guild_dir(dirs, args):
    if args.all or args.sourcecode:
        return
    try:
        dirs.remove(".guild")
    except ValueError:
        pass


def _match_path(filename, pattern):
    if not pattern:
        return True
    return filename.startswith(pattern) or fnmatch.fnmatch(filename, pattern)


def _print_file(path, args):
    if args.full_path:
        path = os.path.abspath(path)
    elif args.sourcecode:
        path = _sourcecode_rel_path(path)
    if not path:
        return
    if args.no_format:
        cli.out(path)
    else:
        cli.out("  %s" % path)


def _sourcecode_rel_path(path):
    prefix = os.path.join(".guild", "sourcecode")
    if path.startswith(prefix):
        return path[len(prefix) + 1 :]
    return path
