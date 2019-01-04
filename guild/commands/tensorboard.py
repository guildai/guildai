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
from . import server_support

@click.command(name="tensorboard")
@runs_support.runs_arg
@server_support.host_and_port_options
@click.option(
    "--refresh-interval", metavar="SECONDS",
    help="Refresh interval (defaults to 5 seconds).",
    type=click.IntRange(1, None),
    default=5)
@click.option(
    "-n", "--no-open",
    help="Don't open TensorBoard in a browser.",
    is_flag=True)
@runs_support.op_and_label_filters
@runs_support.status_filters

@click_util.use_args
@click_util.render_doc

def tensorboard(args):
    """Visualize runs with TensorBoard.

    This command will start a TensorBoard process and open a browser
    window for you. TensorBoard will show the views that are selected
    using the commands filters. This list corresponds to the the runs
    shown when running ``guild runs``.

    This command will not exit until you type ``CTRL-c`` to stop it.

    If you'd like to change the filters used to select runs, stop the
    command and re-run it with a different set of filters. You may
    alternatively start another instance of TensorBoard in a separate
    console.

    TensorBoard will automatically refresh with the current run data.

    If you're prefer that Guild not open a browser window, run the
    command with the `--no-open` option.

    By default, Guild will start the TensorBoard process on a randomly
    selected free port. If you'd like to specify the port that
    TensorBoard runs on, use the ``--port`` option.

    """
    from . import tensorboard_impl
    tensorboard_impl.main(args)
