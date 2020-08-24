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
@runs_support.runs_arg
@click.option(
    "--min",
    "min_col",
    metavar="COLUMN",
    help="Show the lowest values for COLUMN first.",
)
@click.option(
    "--max",
    "max_col",
    metavar="COLUMN",
    help="Show the highest values for COLUMN first.",
)
@click.option(
    "-n",
    "--limit",
    "--top",
    metavar="N",
    type=click.IntRange(min=1),
    help="Only show the top N runs.",
)
@click.option(
    "-e",
    "--extra-cols",
    is_flag=True,
    help="Show extra columns such as source code hash.",
)
@click.option(
    "-s",
    "--all-scalars",
    is_flag=True,
    help="Include all scalars. By default system scalars are omitted.",
)
@click.option(
    "-c",
    "--cols",
    metavar="COLUMNS",
    help=(
        "Comma delimited list of additional columns to compare. "
        "See Column Specs for information on column format. "
        "Cannot be used with --strict-columns."
    ),
)
@click.option(
    "-cc",
    "--strict-cols",
    metavar="COLUMNS",
    help=(
        "Comma delimited list of the columns to compare. "
        "See Column Specs for information on column format. "
        "Cannot be used with --columns."
    ),
)
@click.option(
    "-p", "--skip-op-cols", is_flag=True, help="Don't show operation columns."
)
@click.option("-r", "--skip-core", is_flag=True, help="Don't show core columns.")
@click.option("-t", "--table", is_flag=True, help="Show comparison data as a table.")
@click.option(
    "--csv",
    metavar="PATH",
    help=(
        "Save comparison data to a CSV file. Use '-' for PATH to print to "
        "standard output."
    ),
)
@click.option(
    "--tool",
    metavar="TOOL",
    help="Use TOOL to compare runs. See TOOLS for a list of supported tools",
    type=click.Choice(["hiplot"]),
)
@click.option("--include-batch", is_flag=True, help="Include batch runs.")
@click.option("--print-scalars", is_flag=True, help="Show available scalars and exit.")
@runs_support.all_filters
@click.pass_context
@click_util.use_args
@click_util.render_doc
def compare(ctx, args):
    """Compare run results.

    Guild Compare is a console based application that displays a
    spreadsheet of runs with their current accuracy and loss. The
    application will continue to run until you exit it by pressing
    ``q`` (for quit).

    Guild Compare supports a number of commands. Commands are
    activated by pressing a letter. To view the list of commands,
    press ``?``.

    Guild Compare does not automatically update to display the latest
    available data. If you want to update the list of runs and their
    status, press ``r`` (for refresh).

    You may alternative use the `--csv` option to write a CSV file
    containing the compare data. To print the CSV contents to standard
    output, use '-' for the file path.

    ### Compare Columns

    Guild Compare shows columns for each run based on the columns
    defined for each run operation. Additional columns may be
    specified using the `--columns` option, which must be a comma
    separated list of column specs. See below for column spec details.

    If multiple columns have the same name, they are merged into a
    single column. Cell values are merged by taking the first non-null
    value in the list of cells with the common name from
    left-to-right.

    By default, columns always contain run ID, model, operation,
    started, time, label, status, and the set of columns defined for
    each displayed operation. You can skip the core columns by with
    `--skip-core` and skip the operation columns with
    `--skip-op-cols`.

    ### Column Specs

    Each column specified in `COLUMNS` must be a valid column spec. A
    column spec is the name of a run flag or scalar key. Flag names
    must be preceded by an equals sign ``=`` to differentiate them
    from scalar keys.

    For example, to include the flag ``epochs`` as a column, use
    ``--columns =epochs``.

    If a scalar is specified, it may be preceded by a qualifier of
    `min`, `max`, `first`, `last`, `avg`, `total`, or `count` to
    indicate the type of scalar value. For example, to include the
    highest logged value for `accuracy`, use ``--columns "max
    accuray"``.

    By default `last` is assumed, so that the last logged value for
    the specified scalar is used.

    A scalar spec may additionally contain the key word `step` to
    indicate that the step associated with the scalar is used. For
    example, to include the step of the last `accuracy` value, use
    ``--columns "accuracy step"``. Step may be used with scalar
    qualifiers. For example, to include the value and associated step
    of the lowest loss, use ``--columns "min loss, min loss step"``.

    Column specs may contain an alternative column heading using the
    keyword ``as`` in the format ``COL as HEADING``. Headings that
    contain spaces must be quoted.

    For example, to include the scalar ``val_loss`` with name
    ``validation loss``, use ``--columns val_loss as 'validation
    loss'``.

    You may include run attributes as column specs by preceding the
    run attribute name with a period ``.``. For example, to include
    the `stopped` attribute, use ``--columns .stopped``. This is
    useful when using `--skip-core`.

    ### Sort Runs

    Use `--min` and `--max` to sort results by a particular
    column. `--min` sorts in ascending order and `--max` sorts in
    descending order.

    When specifying `COLUMN`, use the column name as displayed in the
    table output. If the column name contains spaces, quote the value.

    By default, runs are sorted by start time in ascending order -
    i.e. the most recent runs are listed first.

    ### Limit Runs

    To limit the results to the top `N` runs, use `--top`.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.all_filters }}

    ### Tools

    Guild provides support for comparing runs using different
    tools. To use a different tool, specify its name with the `--tool`
    option.

    Supported tools:

    \b
      hiplot   Facebook's HiPlot high dimensionality viewer
               for evaluating hyperparameters.

    ### Show Batch Runs

    By default, batch runs are not included in comparisons. To include
    batch runs, specify `--include-batch`.

    """
    from . import compare_impl

    compare_impl.main(args, ctx)
