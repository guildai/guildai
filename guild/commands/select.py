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

from . import runs_support


# List of formatted run attrs supported by select with attr.
_RUN_UTIL_FORMAT_ATTRS = [
    "command",
    "duration",
    "exit_status",
    "from",
    "id",
    "index",
    "label",
    "marked",
    "model",
    "op_name",
    "operation",
    "pid",
    "pkg_name",
    "run_dir",
    "short_id",
    "sourcecode_digest",
    "started",
    "status",
    "stopped",
    "vcs_commit",
]


def _ac_attr(incomplete, ctx, **_kw):
    attrs = set(_RUN_UTIL_FORMAT_ATTRS)
    runs = runs_support.runs_for_ctx(ctx)
    if runs:
        attrs.update(runs[0].attr_names())
    return sorted([name for name in attrs if name.startswith(incomplete)])


@click.command()
@runs_support.run_arg
@click.option(
    "-min",
    "--min",
    metavar="SCALAR",
    help="Select the run with the lowest value for SCALAR.",
)
@click.option(
    "-max",
    "--max",
    metavar="SCALAR",
    help="Select the run with the highest value for SCALAR.",
)
@click.option("-s", "--short-id", help="Use short ID.", is_flag=True)
@click.option(
    "-a",
    "--attr",
    help="Show specified run attribute rather than run ID.",
    autocompletion=_ac_attr,
)
@runs_support.all_filters
@click.pass_context
@click_util.use_args
@click_util.render_doc
def select(ctx, args):
    """Select a run and shows its ID.

    This command is generally used when specifying a run ID for
    another Guild command. For example, to restart the latest `train`
    run:

        `guild run --restart $(guild select -o train)`

    {{ runs_support.run_arg }}

    If RUN isn't specified, the latest matching run is selected.

    ### Selecting Min or Max Scalar

    To select the run with the lowest or highest scalar value, use
    `--min` or `--max` respectively. For example, to select the run
    with the lowest `loss` scalar value, use `--min loss`.

    Other run filters are applied before selecting a minimum or
    maximium scalar value.

    {{ runs_support.all_filters }}

    """
    from . import runs_impl

    runs_impl.select(args, ctx)
