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
import sys

import click

from guild import cli
from guild import run_util

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")


def main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error("PATH must be relative\nTry 'guild cat --help' for more information.")
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
        cli.error("PATH must be relative\nTry 'guild cat --help' for more information.")
    path_root = _path_root(args, run)
    return os.path.join(path_root, args.path)


def _check_non_output_args(args):
    if args.path or args.sourcecode:
        cli.out(
            "--output cannot be used with other options - ignorning other options",
            err=True,
        )


def _path_root(args, run):
    return run_util.sourcecode_dir(run) if args.sourcecode else run.dir


def _page(path):
    f = _open_file(path)
    click.echo_via_pager(f.read())


def _open_file(path, binary=False):
    mode = "rb" if binary else "r"
    try:
        return open(path, mode)
    except (IOError, OSError) as e:
        if e.errno == 2:
            cli.error(f"{path} does not exist")
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
