# Copyright 2017-2018 TensorHub, Inc.
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

@click.command(name="operations, ops")
@click.argument("filters", metavar="[FILTER]...", required=False, nargs=-1)
@click.option("-v", "--verbose", help="Show operation details.", is_flag=True)

@click_util.use_args

def operations(args):
    """Show model operations.

    Use one or more `FILTER` arguments to show only operations whose
    names or models match the specified values.

    `FILTER` may a directory to indicate that only operations of
    models defined in that location are included in the list.

    """
    from . import operations_impl
    operations_impl.main(args)
