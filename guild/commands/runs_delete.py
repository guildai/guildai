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
from . import remote_support
from . import runs_support

@click.command("delete, rm")
@runs_support.runs_op
@remote_support.remote_option("Delete remote runs.")
@click.option(
    "-y", "--yes",
    help="Do not prompt before deleting.",
    is_flag=True)
@click.option(
    "-p", "--permanent",
    help="Permanentaly delete runs so they cannot be recovered.",
    is_flag=True)

@click.pass_context
@click_util.use_args
@click_util.render_doc

def delete_runs(ctx, args):
    """Delete one or more runs.

    Runs are deleting by specifying `RUN` arguments. If a `RUN`
    argument is not specified, all runs matching the filter criteria
    are deleted. See SPECIFYING RUNS and FILTERING topics for more
    information on how runs are selected.

    By default, Guild will display the list of runs to be deleted and
    ask you to confirm the operation. If you want to delete the runs
    without being prompted, use the ``--yes`` option.

    **WARNING**: Take care when deleting runs using indexes as the
    runs selected with indexes can change. Review the list of runs
    carefully before confirming a delete operation.

    If a run is still running, Guild will stop it first before
    deleting it.

    If you delete a run by mistake, provided you didn't use the
    ``--permanent`` option, you can restore it using ``guild runs
    restore``.

    If you want to permanently delete runs, use the ``--permanent``
    option.

    **WARNING**: Permanentaly deleted runs cannot be restored.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}

    ### Deleting remote runs

    To delete runs on a remote, use `--remote`.

    {{ remote_support.remote_option }}

    """

    from . import runs_impl
    runs_impl.delete_runs(args, ctx)
