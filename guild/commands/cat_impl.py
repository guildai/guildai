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
import sys

import click

from guild import cli

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")


def main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n" "Try 'guild cat --help' for more information."
        )
    if args.remote:
        remote_impl_support.cat(args)
    else:
        _main(args, ctx)


def _main(args, ctx):
    run = runs_impl.one_run(args, ctx)
    path = _path(run, args)
    if args.page:
        _page(path)
    else:
        _cat(path)


def _path(run, args):
    if args.output:
        _check_non_output_args(args)
        return run.guild_path("output")
    if not args.path:
        cli.error("-p / --path is required unless --output is specified")
    if os.path.isabs(args.path):
        cli.error(
            "PATH must be relative\n" "Try 'guild cat --help' for more information."
        )
    return os.path.join(_path_root(args, run), args.path)


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


def _page(path):
    f = _open_file(path)
    click.echo_via_pager(f.read())


def _open_file(path, binary=False):
    mode = "rb" if binary else "r"
    try:
        return open(path, mode)
    except (IOError, OSError) as e:
        if e.errno == 2:
            cli.error("%s does not exist" % path)
        else:
            cli.error(str(e))


def _cat(path):
    f = _open_file(path, binary=True)
    sys.stdout.flush()
    try:
        out = sys.stdout.buffer
    except AttributeError:
        out = sys.stdout
    while True:
        b = f.read(10240)
        if not b:
            break
        out.write(b)
    out.flush()
