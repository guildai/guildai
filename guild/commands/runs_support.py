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

def runs_arg(fn):
    """### Specifying runs

    You may use one or more `RUN` arguments to indicate which runs
    apply to the command. `RUN` may be a run ID, a run ID prefix, or a
    one-based index corresponding to a run returned by the list
    command.

    Indexes may also be specified in ranges in the form `START:END`
    where `START` is the start index and `END` is the end
    index. Either `START` or `END` may be omitted. If `START` is
    omitted, all runs up to `END` are selected. If `END` id omitted,
    all runs from `START` on are selected. If both `START` and `END`
    are omitted (i.e. the ``:`` char is used by itself) all runs are
    selected.

    """
    click_util.append_params(fn, [
        click.Argument(("runs",), metavar="[RUN...]", nargs=-1)
    ])
    return fn

def run_arg(fn):
    """### Specifying a run

    You may specify a run using a run ID, a run ID prefix, or a
    one-based index corresponding to a run returned by the list
    command.

    """
    click_util.append_params(fn, [
        click.Argument(("run",), required=False)
    ])
    return fn

def op_and_label_filters(fn):
    """### Filtering by operation and label

    Runs may be filtered by operation using `--operation`.  A run is
    only included if any part of its full operation name, including
    the package and model name, matches the value.

    Use `--label` to only include runs with labels matching a
    specified value.

    `--operation` and `--label` may be used multiple times to expand
    the runs that are included.

    Use `--unlabeled` to only include runs without labels. This option
    may not be used with `--label`.

    Use `--marked` to only include marked runs.

    """
    click_util.append_params(fn, [
        click.Option(
            ("-o", "--operation", "ops"), metavar="VAL",
            help="Include runs with operations matching `VAL`.",
            multiple=True),
        click.Option(
            ("-l", "--label", "labels"), metavar="VAL",
            help="Include runs with labels matching `VAL`.",
            multiple=True),
        click.Option(
            ("-u", "--unlabeled",),
            help="Include only runs without labels.",
            is_flag=True),
        click.Option(
            ("-M", "--marked",),
            help="Include only marked runs.",
            is_flag=True),
        click.Option(
            ("-U", "--unmarked",),
            help="Include only unmarked runs.",
            is_flag=True),
    ])
    return fn

def status_filters(fn):
    """### Filtering by run status

    Runs may also be filtered by specifying one or more status
    filters: `--running`, `--completed`, `--error`, and
    `--terminated`. These may be used together to include runs that
    match any of the filters. For example to only include runs that
    were either terminated or exited with an error, use ``--terminated
    --error``, or the short form ``-ET``.

    Status filters are applied before `RUN` indexes are resolved. For
    example, a run index of ``1`` is the latest run that matches the
    status filters.

    """
    click_util.append_params(fn, [
        click.Option(
            ("-R", "--running"),
            help="Include only runs that are still running.",
            is_flag=True),
        click.Option(
            ("-C", "--completed"),
            help="Include only completed runs.",
            is_flag=True),
        click.Option(
            ("-E", "--error"),
            help="Include only runs that exited with an error.",
            is_flag=True),
        click.Option(
            ("-T", "--terminated"),
            help="Include only runs terminated by the user.",
            is_flag=True),
        click.Option(
            ("-P", "--pending"),
            help="Include only pending runs.",
            is_flag=True),
    ])
    return fn

def time_filters(fn):
    """### Filtering by run start time

    Use `--started` to limit runs to those that have started within a
    specified period of time.

    You can specify a time period in different ways:

      \b
      after DATETIME
      before DATETIME
      between DATETIME and DATETIME
      N UNIT ago
      after N UNIT ago
      before N UNIT ago
      this UNIT
      last UNIT

    `DATETIME` may be specified as a date in the format ``YY-MM-DD``
    (the leading ``YY-`` may be omitted) or as a time in the format
    ``HH:MM`` (24 hour clock). A date and time may be specified
    together as `DATE TIME`.

    `UNIT` may be ``minutes``, ``hours``, ``days``, ``weeks``,
    ``months``, or ``years``. A unit may be specified without the
    trailing ``s`` for readability.

    When using `between`, `DATETIME` values may be specified in any
    order.

    Special values ``today``, ``yesterday`` may be used for
    readability.

    Examples:

      \b
      after 7-1
      between 1-1 and 4-30
      between 10:00 and 15:00
      3 months ago
      after 10 days ago
      before 10 days ago
      between yesterday and 3 days ago
      this week
      last year

    """
    click_util.append_params(fn, [
        click.Option(
            ("--started",),
            metavar="PERIOD",
            help=(
                "Limit to runs started with PERIOD. See above for "
                "ways to specify PERIOD."))
    ])
    return fn

@click_util.render_doc

def all_filters(fn):
    """
    {{ op_and_label_filters }}
    {{ status_filters }}
    {{ time_filters }}
    """
    click_util.append_params(fn, [
        op_and_label_filters,
        status_filters,
        time_filters,
    ])
    return fn
