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


@click.command(name="view")
@runs_support.runs_arg
@server_support.host_and_port_options
@click.option(
    "-n", "--no-open", help="Don't open Guild View in a browser.", is_flag=True
)
@click.option("--logging", help="Log requests.", is_flag=True)
@runs_support.all_filters
@click.option("--dev", is_flag=True, hidden=True)
@click.option("--test", is_flag=True, hidden=True)
@click.option("--test-runs-data", is_flag=True, hidden=True)
@click_util.use_args
@click_util.render_doc
def view(args):
    """Visualize runs in a local web application.

    Features include:

      \b
      - View and filter runs
      - Compare runs
      - Browse run files
      - View run images and other media
      - View run output

    Guild View does not currently support starting or modifying
    runs. For these operations, use the applicable command line
    interface. Run 'guild help' for a complete list of commands.

    By default Guild View shows all runs. You can filter runs using
    the command options described below.

    {{ runs_support.runs_arg }}

    {{ runs_support.all_filters }}

    """
    from . import view_impl

    view_impl.main(args)
