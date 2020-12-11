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

from guild import cli
from guild import run_util
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
    base_dir = _base_dir(run, args)
    _print_header(base_dir, args)
    _print_file_listing(base_dir, args)


def _base_dir(run, args):
    if args.sourcecode:
        return run_util.sourcecode_dir(run)
    else:
        return run.dir


def _print_header(dir, args):
    if not args.full_path and not args.no_format:
        cli.out("%s:" % _header(dir, args))


def _header(dir, args):
    if os.getenv("NO_HEADER_PATH") == "1":
        dir = os.path.basename(dir)
    if args.full_path:
        return dir
    else:
        return util.format_dir(dir)


def _print_file_listing(dir, args):
    for val in sorted(_list(dir, args)):
        _print_path(val, args)


def _list(dir, args):
    for root, dirs, files in os.walk(dir, followlinks=args.follow_links):
        if root == dir:
            _maybe_rm_guild_dir(dirs, args)
        for name in dirs + files:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, dir)
            if not _match_path(rel_path, args.path):
                continue
            yield _list_path(full_path, rel_path, args)


def _maybe_rm_guild_dir(dirs, args):
    if not args.all and not _wants_guild_files(args.path):
        _rm_guild_dir(dirs)


def _wants_guild_files(path):
    return path and path.startswith(".guild")


def _rm_guild_dir(dirs):
    try:
        dirs.remove(".guild")
    except ValueError:
        pass


def _match_path(filename, pattern):
    return (
        not pattern
        or filename.startswith(pattern)
        or fnmatch.fnmatch(filename, pattern)
    )


def _list_path(full_path, rel_path, args):
    path = full_path if args.full_path else rel_path
    return _ensure_trailing_slash_for_dir(path, full_path)


def _ensure_trailing_slash_for_dir(path, full_path):
    if os.path.isdir(full_path) and full_path[:-1] != os.path.sep:
        return path + os.path.sep
    return path


def _print_path(path, args):
    if args.full_path:
        path = os.path.abspath(path)
    elif args.sourcecode:
        path = _sourcecode_rel_path(path)
    if not path:
        return
    if args.no_format or args.full_path:
        cli.out(path)
    else:
        cli.out("  %s" % path)


def _sourcecode_rel_path(path):
    prefix = os.path.join(".guild", "sourcecode")
    if path.startswith(prefix):
        return path[len(prefix) + 1 :]
    return path
