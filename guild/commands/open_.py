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

import click

from guild import click_util

from . import ac_support
from . import runs_support


def _ac_cmd(ctx, _param, incomplete):
    if ctx.params.get("remote"):
        return []
    return ac_support.ac_command(incomplete)


def _ac_path(ctx, _param, incomplete):
    from guild import run_util
    from . import runs_impl

    open_args = click_util.Args(**ctx.params)
    run = runs_impl.one_run(open_args, ctx)
    dir_base = run_util.sourcecode_dest(run) if open_args.sourcecode else run.dir
    return ac_support.ac_run_filepath(dir_base, incomplete)


@click.command("open")
@runs_support.run_arg
@click.option(
    "-p",
    "--path",
    metavar="PATH",
    shell_complete=_ac_path,
    help="Path to open under run directory.",
)
@click.option(
    "-s", "--sourcecode", is_flag=True, help="Open run source code directory."
)
@click.option(
    "-O",
    "--output",
    is_flag=True,
    help="Open run output. Cannot be used with other options.",
)
@click.option(
    "-c",
    "--cmd",
    metavar="CMD",
    help="Command used to open run.",
    shell_complete=_ac_cmd,
)
@click.option(
    "--shell", is_flag=True, help="Open a new shell in run directory or PATH."
)
@click.option(
    "--shell-cmd",
    metavar="CMD",
    help="Open a new shell in run directory or PATH using CMD.",
)
@runs_support.all_filters
@click.pass_context
@click_util.use_args
@click_util.render_doc
def open_(ctx, args):
    """Open a run path or output.

    This command opens a path a single run.

    {{ runs_support.run_arg }}

    If `RUN` isn't specified, the latest run is selected.

    ### Run Paths

    `--path` may be used to open a path within the run directory. By
    default the run directory itself is opened. PATH must be relative.

    `--sourcecode` may be used to open the run source code
    directory. If `--path` is also specified, the path applies to the
    source code directory rather than the run directory.

    ### Output

    `--output` may be used to open the output for a run. This option
    may not be used with other options.

    ### Open Command

    `--cmd` may be used to specify the command used to open the
    path. By default the system-defined program is used.

    {{ runs_support.all_filters }}

    """
    from . import open_impl

    open_impl.main(args, ctx)
