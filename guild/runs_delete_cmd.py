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

@click.command("delete, rm", help="""
Delete one or more runs.

%s

If a RUN is not specified, assumes all runs (i.e. as if ':' was
specified).
""" % guild.runs_cmd_support.RUN_ARG_HELP)
@click.argument("runs", metavar="[RUN...]",  nargs=-1)
@guild.runs_cmd_support.run_scope_options
@guild.runs_cmd_support.run_filters
@click.option(
    "-y", "--yes",
    help="Do not prompt before deleting.",
    is_flag=True)

@click.pass_context
@guild.click_util.use_args

def delete_runs(ctx, args):
    # Help defined in command decorator.
    import guild.runs_cmd_impl
    guild.runs_cmd_impl.delete_runs(args, ctx)
