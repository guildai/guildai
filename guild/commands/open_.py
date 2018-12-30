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

@click.command("open")
@runs_support.run_arg
@click.option(
    "-p", "--path",
    metavar="PATH", help="Path to open under run directory.")
@click.option(
    "-s", "--source",
    is_flag=True,
    help="Open run source directory.")
@click.option(
    "-c", "--cmd", metavar="CMD",
    help="Command used to open run.")
@runs_support.op_and_label_filters
@runs_support.status_filters

@click.pass_context
@click_util.use_args
@click_util.render_doc

def open_(ctx, args):
    """Open a run path.

    This command opens a path a single run.

    {{ runs_support.run_arg }}

    If `RUN` isn't specified, the latest run is selected.

    ### Run paths

    `--path` may be used to open a path within the run directory. By
    default the run directory itself is opened. PATH must be relative.

    `--source` may be used to open the run source directory. If
    `--path` is also specified, the path applies to the source
    directory rather than the run directory.

    ### Open command

    `--cmd` may be used to specify the command used to open the
    path. By default the system-defined program is used.

    """
    from . import open_impl
    open_impl.main(args, ctx)
