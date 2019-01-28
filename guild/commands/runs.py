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

from guild import cli
from guild import click_util

from .runs_delete import delete_runs
from .runs_diff import diff_runs
from .runs_export import export_runs
from .runs_import import import_runs
from .runs_info import run_info
from .runs_label import label_runs
from .runs_list import list_runs, runs_list_options
from .runs_mark import mark_runs
from .runs_pull import pull_runs
from .runs_purge import purge_runs
from .runs_push import push_runs
from .runs_restore import restore_runs
from .runs_stop import stop_runs

@click.group(invoke_without_command=True, cls=click_util.Group)
@runs_list_options

@click.pass_context

def runs(ctx, **kw):
    """Show or manage runs.

    If `COMMAND` is omitted, lists runs. Refer to ``guild runs list
    --help`` for more information on the `list` command.

    """
    if not ctx.invoked_subcommand:
        ctx.invoke(list_runs, **kw)
    else:
        if _params_specified(kw):
            # TODO: It'd be nice to move kw over to the subcommand.
            cli.error(
                "options cannot be listed before command ('%s')"
                % ctx.invoked_subcommand)

def _params_specified(kw):
    return any((kw[key] for key in kw))

runs.add_command(delete_runs)
runs.add_command(diff_runs)
runs.add_command(export_runs)
runs.add_command(run_info)
runs.add_command(import_runs)
runs.add_command(label_runs)
runs.add_command(list_runs)
runs.add_command(mark_runs)
runs.add_command(pull_runs)
runs.add_command(purge_runs)
runs.add_command(push_runs)
runs.add_command(restore_runs)
runs.add_command(stop_runs)
