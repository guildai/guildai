# Copyright 2017-2022 RStudio, PBC
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

import click

from guild import click_util

from . import api_support
from . import runs_support


@click.command("compare")
@api_support.output_options
@runs_support.runs_arg
@click.option("--include-batch", is_flag=True, help="Include batch runs.")
@runs_support.all_filters
@click_util.use_args
@click_util.render_doc
def main(args):
    """Show comparison matric as JSON."""
    api_support.out(_compare_data(args), args)


def _compare_data(args):
    from .compare_impl import get_compare_data

    data = get_compare_data(_compare_args_with_id(args), format_cells=False)
    return _relocate_id_col_to_run_col(data)


def _compare_args_with_id(args):
    """Returns args for compare command that can be used to get compare data.

    Includes an additional `.id` column at the end of the default
    columns to get the full run ID.
    """
    return click_util.Args(
        extra_cols=False,
        cols=(".id",),
        strict_cols=None,
        top=None,
        min_col=None,
        max_col=None,
        limit=None,
        skip_core=False,
        skip_op_cols=False,
        all_scalars=False,
        skip_unchanged=False,
        **args.as_kw()
    )


def _relocate_id_col_to_run_col(compare_data):
    """Returns transformated compare data to include the full run ID as the first col.

    Compare data uses the short run ID to represent a 'run'. The short
    run ID is more suitable for typical compare use cases, where the
    data is formatted for the user. In the case of the API, we want to
    provide the full run ID, so we include the `id` run attribute (the
    full run ID) using the `-c` option, which appends that column to
    the compare data.

    This function relocated the last column (the full ID) to the first
    column (the short ID).
    """
    if compare_data[0][0] == "no runs":
        return []
    assert compare_data[0][0] == "run" and compare_data[0][-1] == "id", compare_data[0]
    return [row[-1:] + row[1:-1] for row in compare_data]
