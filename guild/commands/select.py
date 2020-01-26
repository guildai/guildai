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


@click.command()
@runs_support.run_arg
@click.option("-S", "--short", help="Use short ID.", is_flag=True)
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

    {{ runs_support.all_filters }}

    """
    from . import runs_impl

    runs_impl.select_run(args, ctx)
