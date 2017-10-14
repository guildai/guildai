# Copyright 2017 TensorHub, Inc.
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

import guild.click_util
import guild.runs_cmd_support

@click.command()
@guild.runs_cmd_support.run_scope_options
@guild.runs_cmd_support.run_filters
@click.option(
    "--host",
    help="Name of host interface to listen on.")
@click.option(
    "--port",
    help="Port to listen on.",
    type=click.IntRange(0, 65535))
@click.option(
    "--refresh-interval",
    help="Refresh interval (defaults to 5 seconds).",
    type=click.IntRange(1, None),
    default=5)
@click.option(
    "-n", "--no-open",
    help="Don't open the TensorBoard URL in a brower.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def view(ctx, args):
    """Visualize runs with TensorBoard.
    """
    import guild.view_cmd_impl
    guild.view_cmd_impl.main(args, ctx)
