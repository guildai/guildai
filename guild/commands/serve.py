# Copyright 2017-2018 TensorHub, Inc.
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

@click.command()
@runs_support.run_arg
@click.option(
    "-m", "--model", metavar="PATH",
    help="Serve saved model in PATH instead of from a run")
@click.option(
    "-t", "--model-tags", "tags", metavar="TAGS",
    default="serve",
    help=(
        "Tags for the model in PATH to serve, separated by commas "
        "(default is 'serve')."))
@server_support.host_and_port_options
@click.option(
    "-n", "--no-open",
    help="Don't open Guild Serve in a browser.",
    is_flag=True)
@runs_support.op_and_label_filters
@runs_support.status_filters
@runs_support.scope_options
@click.option(
    "--print-model-info", is_flag=True,
    help="Show model info and exit.")

@click.pass_context
@click_util.use_args
@click_util.render_doc

def serve(ctx, args):
    """Serve a saved model.

    By default, or if RUN is specified, serves a saved model generated
    by a run. Use `--saved-model` to specify a saved model path.

    {{ runs_support.run_arg }}

    If RUN isn't specified, the latest run is selected.

    ### Additional information

    You can show additional run information by specifying option
    flags. You may use multiple flags to show more information. Refer
    to the options below for what additional information is available.

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}
    {{ runs_support.scope_options }}

    """
    from . import serve_impl
    serve_impl.main(args, ctx)
