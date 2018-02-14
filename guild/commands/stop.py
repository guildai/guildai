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

@click.command(name="stop")
@click.argument("runs", metavar="[RUN...]", nargs=-1, required=True)
@runs_support.run_scope_options
@click.option(
    "-n", "--no-wait",
    help="Don't wait for remote runs to stop.",
    is_flag=True)
@click.option(
    "-y", "--yes",
    help="Do not prompt before stopping.",
    is_flag=True)

@click_util.use_args

def stop(args):
    """Stop one or more runs.

    RUN must be a valid run ID.

    Stopped runs are ignored.

    """
    from . import stop_impl
    stop_impl.main(args)
