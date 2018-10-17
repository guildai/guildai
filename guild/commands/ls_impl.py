# Copyright 2017-2018 TensorHub, Inc.
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
    path = run.path
    if args.path:
        path = os.path.join(path, args.path)
    _print_header(path, args)
    for val in sorted(_list(path, args)):
        _print_file(val, args)

def _list(path, args):
    for root, dirs, files in os.walk(path, followlinks=args.follow_links):
        _maybe_rm_guild_dir(dirs, args)
        for name in (dirs + files):
            full_path = os.path.join(root, name)
            if os.path.isdir(full_path):
                suffix = os.path.sep
            else:
                suffix = ""
            if args.full_path:
                yield full_path + suffix
            else:
                yield os.path.relpath(full_path, path) + suffix

def _maybe_rm_guild_dir(dirs, args):
    if args.all:
        return
    try:
        dirs.remove(".guild")
    except ValueError:
        pass

def _print_header(path, args):
    if not args.no_format:
        if not args.full_path:
            path = util.format_dir(path)
        cli.out("%s:" % path)

def _print_file(path, args):
    if args.no_format:
        cli.out(path)
    else:
        cli.out("  %s" % path)
