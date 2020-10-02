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

from . import remote_support
from . import runs_support


def runs_stop_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            runs_support.common_filters,
            remote_support.remote_option("Stop remote runs."),
            click.Option(
                ("-y", "--yes"), help="Do not prompt before stopping.", is_flag=True
            ),
            click.Option(
                ("-n", "--no-wait"),
                help="Don't wait for remote runs to stop.",
                is_flag=True,
            ),
        ],
    )
    return fn


@click.command(name="stop")
@runs_stop_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def stop_runs(ctx, args):
    """Stop one or more runs.

    Runs are stopped by specifying one or more RUN arguments. See
    SPECIFYING RUNS and FILTER topics for information on specifying
    runs to be stopped.

    Only runs with status of 'running' are considered for this
    operation.

    If `RUN` is not specified, the latest selected run is stopped.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``1`` is assumed (the most
    recent run with status 'running').

    {{ runs_support.common_filters }}

    ### Stop Remote Runs

    To stop remote runs, use `--remote`.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl

    runs_impl.stop_runs(args, ctx)
