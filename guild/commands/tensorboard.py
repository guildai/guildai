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

from . import runs_support
from . import server_support


@click.command(name="tensorboard")
@runs_support.runs_arg
@server_support.host_and_port_options
@click.option("--include-batch", is_flag=True, help="Include batch runs.")
@click.option(
    "--refresh-interval",
    metavar="SECONDS",
    help="Refresh interval (defaults to 5 seconds).",
    type=click.IntRange(1, None),
    default=5,
)
@click.option(
    "--run-name-flags",
    metavar="FLAGS",
    help="Comma or space delimited list of flags used for run names.",
)
@click.option(
    "-n", "--no-open", help="Don't open TensorBoard in a browser.", is_flag=True
)
@click.option(
    "-O",
    "tensorboard_options",
    metavar="OPTION=VALUE",
    multiple=True,
    help=(
        "An option that is passed through to TensorBoard as --OPTION=VALUE. May be "
        "used multiple times."
    ),
)
@click.option(
    "--skip-images", is_flag=True, help="Don't include run images as TF summaries."
)
@click.option(
    "--skip-hparams", is_flag=True, help="Don't generate HParam TF summaries."
)
@click.option("--tab", metavar="TAB", help="Open with an initially selected tab.")
@click.option(
    "--export-scalars",
    metavar="PATH",
    help=(
        "Export all scalars for a run to a CSV file. Use '-' to write "
        "to standard output."
    ),
)
@runs_support.all_filters
@click.option("--keep-logdir", is_flag=True, hidden=True)
@click.option("--check", is_flag=True, hidden=True)
@click_util.use_args
@click_util.render_doc
def tensorboard(args):
    """Visualize runs with TensorBoard.

    This command will start a TensorBoard process and open a browser
    window for you. TensorBoard will show the views that are selected
    using the commands filters. This list corresponds to the the runs
    shown when running ``guild runs``.

    This command will not exit until you type ``Ctrl-c`` to stop it.

    If you'd like to change the filters used to select runs, stop the
    command and re-run it with a different set of filters. You may
    alternatively start another instance of TensorBoard in a separate
    console.

    TensorBoard will automatically refresh with the current run data.

    If you're prefer that Guild not open a browser window, run the
    command with the `--no-open` option.

    By default, Guild will start the TensorBoard process on a randomly
    selected free port. If you'd like to specify the port that
    TensorBoard runs on, use the `--port` option.

    Guild will not include batch runs by default. To include batch
    runs, use `--include-batch`.

    {{ runs_support.runs_arg }}

    {{ runs_support.all_filters }}
    """
    from . import tensorboard_impl

    tensorboard_impl.main(args)
