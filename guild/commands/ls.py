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

import click

from guild import click_util

from . import runs_support

@click.command("ls")
@runs_support.run_arg
@click.option(
    "-p", "--path",
    metavar="PATH",
    help="Path to list.")
@click.option(
    "-s", "--source",
    is_flag=True,
    help="List source files.")
@click.option(
    "-a", "--all",
    is_flag=True,
    help="Show all files including Guild files.")
@click.option(
    "-f", "--full-path",
    is_flag=True,
    help="Show full path for files.")
@click.option(
    "-L", "--follow-links",
    is_flag=True,
    help="Follow links.")
@click.option(
    "-n", "--no-format",
    is_flag=True,
    help="Show files without additional formatting.")
@runs_support.op_and_label_filters
@runs_support.status_filters

@click.pass_context
@click_util.use_args
@click_util.render_doc

def ls(ctx, args):
    """List run files.

    `--path` may be specified as a relative path pattern to limit
    results within the run directory to matching files.

    `--source` limits the results to run source files. If `--path` is
    specified with `--source`, the path pattern limits results within
    the source directory rather than the run directory.

    {{ runs_support.run_arg }}

    If `RUN` isn't specified, the latest run is selected.

    """
    from . import ls_impl
    ls_impl.main(args, ctx)
