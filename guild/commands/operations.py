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

@click.command(name="operations, ops")
@click.argument("filters", metavar="[FILTER]...", required=False, nargs=-1)
@click.option(
    "-p", "--path", metavar="DIR", multiple=True,
    help="Show operations in DIR. May be used more than once.")
@click.option(
    "-a", "--all", is_flag=True,
    help="Show all operations including those designated as private.")
@click.option("-v", "--verbose", help="Show operation details.", is_flag=True)

@click_util.use_args

def operations(args):
    """Show model operations.

    Use one or more `FILTER` arguments to show only operations whose
    names or models match the specified values.

    Use --path to view operations defined in the specified directory.
    """
    from . import operations_impl
    operations_impl.main(args)
