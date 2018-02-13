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

from __future__ import absolute_import
from __future__ import division

import click

from guild import click_util
from . import runs_support

@click.command()
@click.argument("runs", metavar="[RUN...]", nargs=-1)
@runs_support.run_scope_options
@runs_support.run_filters
@click.argument("label", required=False)
@click.option("--clear", is_flag=True, help="Clear the run's label.")
@click.option(
    "-y", "--yes",
    help="Do not prompt before modifying labels.",
    is_flag=True)

@click.pass_context
@click_util.use_args

def label(ctx, args):
    """Set run labels.
    """
    from . import runs_impl
    runs_impl.label(args, ctx)
