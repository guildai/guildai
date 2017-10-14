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

@click.command("list, ls")
@guild.runs_cmd_support.runs_list_options

@click.pass_context
@guild.click_util.use_args

def list_runs(ctx, args):
    """List runs.

    By default lists runs associated with models defined in the
    current directory, or LOCATION if specified. To list all runs, use
    the --system option.

    To list deleted runs, use the --deleted option. Note that runs are
    still limited to the specified project unless --system is
    specified.

    You may apply any of the filter options below to limit the runs
    listed.
    """
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.list_runs(args, ctx)
