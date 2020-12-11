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

import click

from guild import click_util

from . import remote_support
from . import runs_support


def _ac_run_path(args, ctx, **_kw):
    ctx = runs_support.fix_ac_ctx_for_args(ctx, args)
    if ctx.params.get("remote"):
        return []
    if not ctx.params["run"]:
        ctx.params["run"] = "1"
    run = runs_support.run_for_ctx(ctx)
    if not run:
        return []
    base_dir = _run_base_dir(run, ctx)
    return click_util.completion_run_filepath(base_dir)


def _run_base_dir(run, ctx):
    from . import ls_impl

    args = click_util.Args(**ctx.params)
    return ls_impl._base_dir(run, args)


@click.command("ls")
@runs_support.run_arg
@click.option(
    "-p",
    "--path",
    metavar="PATH",
    help="Path to list.",
    autocompletion=_ac_run_path,
)
@click.option("-s", "--sourcecode", is_flag=True, help="List source code files.")
@click.option("-a", "--all", is_flag=True, help="Show all files including Guild files.")
@click.option("-f", "--full-path", is_flag=True, help="Show full path for files.")
@click.option("-L", "--follow-links", is_flag=True, help="Follow links.")
@click.option(
    "-n", "--no-format", is_flag=True, help="Show files without additional formatting."
)
@click.option(
    "-h",
    "--human-readable",
    is_flag=True,
    help="Show human readable sizes when -x is used.",
)
@runs_support.all_filters
@remote_support.remote_option("List files for for remote run.")
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

    {{ runs_support.all_filters }}

    ### Remote Runs

    Use `--remote` to list files for a remote run.

    {{ remote_support.remote_option }}

    """
    from . import ls_impl

    ls_impl.main(args, ctx)
