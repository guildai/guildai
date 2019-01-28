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

def mark_params(fn):
    click_util.append_params(fn, [
        runs_support.runs_arg,
        runs_support.op_and_label_filters,
        runs_support.status_filters,
        click.Option(
            ("-c", "--clear"),
            help="Clear the run's selected designation.",
            is_flag=True),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before modifying runs.",
            is_flag=True),
    ])
    return fn

@click.command("mark")
@mark_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def mark_runs(ctx, args):
    """Mark a run.

    Marked runs are used to resolve operation dependencies. If a run
    for a required operation is marked, it is used rather than the
    latest run.

    Marked runs may be viewed when listing runs using the `--marked`
    option.

    To unmark the run, use `--clear`.

    {{ runs_support.run_arg }}

    If `RUN` isn't specified, the latest run is used.

    """
    from . import runs_impl
    runs_impl.mark(args, ctx)
