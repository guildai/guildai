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

@click.command("purge")
@runs_support.runs_op
@remote_support.remote_option("Permanently delete remote runs.")
@click.option(
    "-y", "--yes",
    help="Do not prompt before purging.",
    is_flag=True)

@click.pass_context
@click_util.use_args
@click_util.render_doc

def purge_runs(ctx, args):
    """Permanentaly delete one or more deleted runs.

    **WARNING**: Purged runs cannot be recovered!

    Runs are purged (i.e. permanently deleted) by specifying `RUN`
    arguments. If a `RUN` argument is not specified, all runs matching
    the filter criteria are purged. See SPECIFYING RUNS and FILTERING
    topics for more information on how runs are selected.

    Use ``guild runs list --deleted`` for a list of runs that can be
    purged.

    By default, Guild will display the list of runs to be purged and
    ask you to confirm the operation. If you want to purge the runs
    without being prompted, use the ``--yes`` option.

    **WARNING**: Take care when purging runs using indexes as the runs
    selected with indexes can change. Review the list of runs
    carefully before confirming a purge operation.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}

    ### Permanently deleting remote runs

    If a run has been deleted remotely, you can permanently delete it
    using `--remote` provided the remote type supports deleted run
    recovery.

    {{ remote_support.remote_option }}

    """

    from . import runs_impl
    runs_impl.purge_runs(args, ctx)
