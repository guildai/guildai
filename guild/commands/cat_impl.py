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
import sys

import click

from guild import cli

from . import runs_impl

log = logging.getLogger("guild")

def main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n"
            "Try 'guild cat --help' for more information.")
    run = runs_impl.one_run(args, ctx)
    path = _path(run, args)
    if args.page:
        _page(path)
    else:
        _cat(path)

def _path(run, args):
    if args.source:
        root = run.guild_path("source")
    else:
        root = run.path
    return os.path.join(root, args.path)

def _page(path):
    f = _open_file(path)
    click.echo_via_pager(f.read())

def _open_file(path):
    try:
        return open(path, "r")
    except IOError as e:
        cli.error(e)

def _cat(path):
    f = _open_file(path)
    for line in f.readlines():
        sys.stdout.write(line)
    sys.stdout.flush()
