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

@click.command()
@click.argument("filters", metavar="[FILTER]...", required=False, nargs=-1)
@click.option("-a", "--all", help="Show all resources.", is_flag=True)
@click.option("-v", "--verbose", help="Show resource details.", is_flag=True)

@click_util.use_args

def resources(args):
    """Show available resources.

    By default Guild will show resources defined in the current directory
    Use --all to show all resources.
    """
    from . import resources_impl
    resources_impl.main(args)
