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

@click.command(name="view")
@runs_support.runs_arg
@server_support.host_and_port_options
@click.option(
    "-n", "--no-open",
    help="Don't open Guild View in a browser.",
    is_flag=True)
@click.option("--logging", help="Log requests.", is_flag=True)
@click.option(
    "--files",
    help=(
        "View run files using file browser rather than start Guild "
        "View. Guild View related options (`--no-open`, `--logging`) "
        "are ignored."),
    is_flag=True)
@runs_support.op_and_label_filters
@runs_support.status_filters
@click.option("--dev", is_flag=True, hidden=True)
@click.option("--test", is_flag=True, hidden=True)

@click_util.use_args
@click_util.render_doc

def view(args):
    """Visualize runs.
    """
    from . import view_impl
    view_impl.main(args)
