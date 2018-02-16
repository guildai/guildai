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
@click.argument("filters", metavar="[FILTER]...", required=False, nargs=-1)
@runs_support.run_scope_options
@runs_support.run_filters
@click.option(
    "--csv", "format", flag_value="csv",
    help="Generate comparison data as a CSV file.",
    is_flag=True)

@click_util.use_args

def compare(args):
    """Compare run results.

    Guild Compare is a console based application that displays a table
    of runs with their current accuracy and loss. The application will
    continue to run until you exit it by pressing ``q`` (for quit).

    Guild Compare supports a number of commands. Commands are
    activated by pressing a letter. To view the list of commands,
    press ``?``.

    Guild Compare does not automatically update to display the latest
    available data. If you want to update the list of runs and their
    status, press ``r`` (for refresh).

    You may alternative use this command to generate CSV output for
    run. Use the `--csv` option to print data to standard output
    instead of running as an application. You can redirect this output
    to a file using ``guild compare --csv > RUNS.csv``.

    `FILTER` may be used to filter the runs compared. Use this value
    to select runs with a particular operation or label.

    """
    from . import compare_impl
    compare_impl.main(args)
