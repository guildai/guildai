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
            ("--unlabeled",),
            help="Include only runs without labels.",
            is_flag=True),
        click.Option(
            ("--marked",),
            help="Include only marked runs.",
            is_flag=True),
        click.Option(
            ("--unmarked",),
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

def runs_op(fn):
    click_util.append_params(fn, [
        runs_arg,
        op_and_label_filters,
        status_filters,
    ])
    return fn
