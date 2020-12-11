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
    if ctx.params["remote"]:
        return []
    if ctx.params["output"]:
        return []
    if not ctx.params["run"]:
        ctx.params["run"] = "1"
    run = runs_support.run_for_ctx(ctx)
    if not run:
        return []
    base_dir = _run_base_dir(run, ctx)
    return click_util.completion_run_filepath(base_dir)


def _run_base_dir(run, ctx):
    from . import cat_impl

    args = click_util.Args(**ctx.params)
    return cat_impl._path_root(args, run)


@click.command("cat")
@runs_support.run_arg
@click.option(
    "-p",
    "--path",
    metavar="PATH",
    help="Path of file to show. Require unless --output is used.",
    autocompletion=_ac_run_path,
)
@click.option(
    "-s", "--sourcecode", is_flag=True, help="Apply PATH to source code files."
)
@click.option(
    "-O", "--output", is_flag=True, help="Show run output. Cannot be used with --path."
)
@click.option("-pa", "--page", is_flag=True, help="Show file in pager.")
@runs_support.all_filters
@remote_support.remote_option("Show contents of a remote run file.")
@click.pass_context
@click_util.use_args
@click_util.render_doc
def cat(ctx, args):
    """Show contents of a run file.

    {{ runs_support.run_arg }}

    If `RUN` isn't specified, the latest run is selected.

    `-p, --path` is required unless `--output` is used. `PATH` must be
    a relative path to a file in the specified run directory or to the
    run source directory if `--sourcecode` is specified.

    `--sourcecode` may be used to show a source code file.

    `--output` may be used to show output for a run. This option
    may not be used with other options.

    {{ runs_support.all_filters }}

    """
    from . import cat_impl

    cat_impl.main(args, ctx)
