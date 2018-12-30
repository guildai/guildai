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

import fnmatch
import logging
import os

from guild import cli
from guild import util

from . import runs_impl

log = logging.getLogger("guild")

def main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n"
            "Try 'guild ls --help' for more information.")
    run = runs_impl.one_run(args, ctx)
    _print_header(run.path, args)
    for val in sorted(_list(run.path, args)):
        _print_file(val, args)

def _print_header(run_dir, args):
    if not args.full_path and not args.no_format:
        if not args.full_path:
            run_dir = util.format_dir(run_dir)
        cli.out("%s:" % run_dir)

def _list(run_dir, args):
    match_path_pattern = _match_path_pattern(args)
    for root, dirs, files in os.walk(run_dir, followlinks=args.follow_links):
        _maybe_rm_guild_dir(dirs, args)
        for name in (dirs + files):
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

def _match_path_pattern(args):
    pattern = args.path
    if args.source:
        source_base = os.path.join(".guild", "source")
        if pattern:
            pattern = os.path.join(source_base, pattern)
        else:
            pattern = source_base
    return pattern

def _maybe_rm_guild_dir(dirs, args):
    if args.all or args.source:
        return
    try:
        dirs.remove(".guild")
    except ValueError:
        pass

def _match_path(filename, pattern):
    if not pattern:
        return True
    return (
        filename.startswith(pattern) or
        fnmatch.fnmatch(filename, pattern))

def _print_file(path, args):
    if args.full_path:
        cli.out(os.path.abspath(path))
    elif args.no_format:
        cli.out(path)
    else:
        cli.out("  %s" % path)
