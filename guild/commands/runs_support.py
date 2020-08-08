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


def _ac_run(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = _ac_runs_for_ctx(ctx)
    return sorted([run.id for run in runs if run.id.startswith(incomplete)])


def _ac_runs_for_ctx(ctx):
    from guild import config
    from guild.commands import runs_impl

    param_args = click_util.Args(**ctx.params)
    with config.SetGuildHome(ctx.parent.params.get("guild_home")):
        return runs_impl.filtered_runs(param_args, ctx=ctx)


def _ac_operation(ctx, incomplete, **_kw):
    from guild import run_util

    if ctx.params.get("remote"):
        return []
    runs = _ac_runs_for_ctx(ctx)
    ops = set([run_util.format_operation(run, nowarn=True) for run in runs])
    return sorted([op for op in ops if op.startswith(incomplete)])


def _ac_label(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = _ac_runs_for_ctx(ctx)
    labels = set([run.get("label") or "" for run in runs])
    return sorted([_quote_label(l) for l in labels if l and l.startswith(incomplete)])


def _quote_label(l):
    return "\"%s\"" % l


def _ac_digest(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = _ac_runs_for_ctx(ctx)
    digests = set([run.get("sourcecode_digest") or "" for run in runs])
    return sorted([d for d in digests if d and d.startswith(incomplete)])


def runs_arg(fn):
    """### Specify Runs

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
    click_util.append_params(
        fn,
        [
            click.Argument(
                ("runs",), metavar="[RUN...]", nargs=-1, autocompletion=_ac_run
            )
        ],
    )
    return fn


def run_arg(fn):
    """### Specify a Run

    You may specify a run using a run ID, a run ID prefix, or a
    one-based index corresponding to a run returned by the `list`
    command.

    """
    click_util.append_params(
        fn, [click.Argument(("run",), required=False, autocompletion=_ac_run)]
    )
    return fn


def op_and_label_filters(fn):
    """### Filter by Operation or Label

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
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-o", "--operation", "ops"),
                metavar="VAL",
                help="Filter runs with operations matching `VAL`.",
                multiple=True,
                autocompletion=_ac_operation,
            ),
            click.Option(
                ("-l", "--label", "labels"),
                metavar="VAL",
                help="Filter runs with labels matching `VAL`.",
                multiple=True,
                autocompletion=_ac_label,
            ),
            click.Option(
                ("-U", "--unlabeled",),
                help="Filter only runs without labels.",
                is_flag=True,
            ),
            click.Option(
                ("-M", "--marked",), help="Filter only marked runs.", is_flag=True
            ),
            click.Option(
                ("-N", "--unmarked",), help="Filter only unmarked runs.", is_flag=True
            ),
        ],
    )
    return fn


def status_filters(fn):
    """### Filter by Run Status

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
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-R", "--running"),
                help="Filter only runs that are still running.",
                is_flag=True,
            ),
            click.Option(
                ("-C", "--completed"), help="Filter only completed runs.", is_flag=True
            ),
            click.Option(
                ("-E", "--error"),
                help="Filter only runs that exited with an error.",
                is_flag=True,
            ),
            click.Option(
                ("-T", "--terminated"),
                help="Filter only runs terminated by the user.",
                is_flag=True,
            ),
            click.Option(
                ("-P", "--pending"), help="Filter only pending runs.", is_flag=True
            ),
            click.Option(
                ("-G", "--staged"), help="Filter only staged runs.", is_flag=True
            ),
        ],
    )
    return fn


def time_filters(fn):
    """### Filter by Run Start Time

    Use `--started` to limit runs to those that have started within a
    specified time range.

    **IMPORTANT:** You must quote RANGE values that contain
    spaces. For example, to filter runs started within the last hour,
    use the option:

        --selected 'last hour'

    You can specify a time range using several different forms:

      \b
      `after DATETIME`
      `before DATETIME`
      `between DATETIME and DATETIME`
      `last N minutes|hours|days`
      `today|yesterday`
      `this week|month|year`
      `last week|month|year`
      `N days|weeks|months|years ago`

    `DATETIME` may be specified as a date in the format ``YY-MM-DD``
    (the leading ``YY-`` may be omitted) or as a time in the format
    ``HH:MM`` (24 hour clock). A date and time may be specified
    together as `DATE TIME`.

    When using ``between DATETIME and DATETIME``, values for
    `DATETIME` may be specified in either order.

    When specifying values like ``minutes`` and ``hours`` the training
    ``s`` may be omitted to improve readability. You may also use
    ``min`` instead of ``minutes`` and ``hr`` instead of ``hours``.

    Examples:

      \b
      `after 7-1`
      `after 9:00`
      `between 1-1 and 4-30`
      `between 10:00 and 15:00`
      `last 30 min`
      `last 6 hours`
      `today`
      `this week`
      `last month`
      `3 weeks ago`

    """
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-S", "--started",),
                metavar="RANGE",
                help=(
                    "Filter only runs started within RANGE. See above "
                    "for valid time ranges."
                ),
            )
        ],
    )
    return fn


def sourcecode_digest_filters(fn):
    """### Filter by Source Code Digest

    To show runs for a specific source code digest, use `-g` or
    `--digest` with a complete or partial digest value.

    """
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-D", "--digest",),
                metavar="VAL",
                help=("Filter only runs with a matching source code digest."),
                autocompletion=_ac_digest,
            )
        ],
    )
    return fn


@click_util.render_doc
def all_filters(fn):
    """
    {{ op_and_label_filters }}
    {{ status_filters }}
    {{ time_filters }}
    {{ sourcecode_digest_filters }}
    """
    click_util.append_params(
        fn,
        [
            op_and_label_filters,
            status_filters,
            time_filters,
            sourcecode_digest_filters,
        ],
    )
    return fn
