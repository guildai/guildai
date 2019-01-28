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

@click.command("restore")
@runs_support.runs_op
@remote_support.remote_option("Restore remote runs.")
@click.option(
    "-y", "--yes",
    help="Do not prompt before restoring.",
    is_flag=True)

@click.pass_context
@click_util.use_args
@click_util.render_doc

def restore_runs(ctx, args):
    """Restore one or more deleted runs.

    Runs are restored using `RUN` arguments. If a `RUN` argument is
    not specified, all runs matching the filter criteria are
    restored. See SPECIFYING RUNS and FILTERING topics for more
    information.

    Use ``guild runs list --deleted`` for a list of runs that can be
    restored.

    By default, Guild will display the list of runs to be restored and
    ask you to confirm the operation. If you want to restore the runs
    without being prompted, use the ``--yes`` option.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}

    ### Restoring remote runs

    If a run has been deleted remotely, you can restore it using
    `--remote` provided the remote type supports this feature.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl
    runs_impl.restore_runs(args, ctx)
