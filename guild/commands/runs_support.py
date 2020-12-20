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

import logging
import sys

import click

from guild import click_util

log = logging.getLogger("guild")


def fix_ac_ctx_for_args(ctx, args):
    """Fixes ctx to ensure ctx.params reflects provided args."""
    cmd_args = _cmd_args(args, ctx)
    fixed_args = _fix_args_for_resilient_parsing(cmd_args)
    fixed_ctx = ctx.command.make_context("", fixed_args, resilient_parsing=True)
    fixed_ctx.parent = ctx.parent
    return fixed_ctx


def _cmd_args(args, ctx):
    cmd_path = ctx.command_path.split(" ")
    assert cmd_path and cmd_path[0] == "guild", cmd_path
    assert args[: len(cmd_path) - 1] == cmd_path[1:], (args, cmd_path)
    return args[len(cmd_path) - 1 :]


def _fix_args_for_resilient_parsing(args):
    """Fixes args for use by Click's resilient parsing.

    If the last argument is missing a value, the Click command does
    not properly parse arguments. In this case we append a dummy
    argument that serves as a placeholder for the parser. As resilient
    parsing is assumed, the dummy option is not validated.
    """
    if args and args[-1][0] == "-":
        return args + ["dummy"]
    return args


def ac_run(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = runs_for_ctx(ctx)
    return sorted([run.id for run in runs if run.id.startswith(incomplete)])


def ac_local_run(ctx, incomplete, **_kw):
    runs = runs_for_ctx(ctx)
    return sorted([run.id for run in runs if run.id.startswith(incomplete)])


def runs_for_ctx(ctx):
    from guild import config
    from . import runs_impl

    args = _runs_args_for_ctx(ctx)
    with config.SetGuildHome(ctx.parent.params.get("guild_home")):
        try:
            return runs_impl.runs_for_args(args, ctx=ctx)
        except SystemExit:
            # Raised when cannot find runs for args.
            return []


def _runs_args_for_ctx(ctx):
    args = click_util.Args(**ctx.params)
    if not hasattr(args, "runs"):
        assert hasattr(args, "run"), "missing runs or run param in %s" % ctx.params
        args.runs = (args.run,) if args.run else ()
    return args


def run_for_ctx(ctx):
    runs = runs_for_ctx(ctx)
    return runs[0] if runs else None


def ac_operation(ctx, incomplete, **_kw):
    from guild import run_util

    if ctx.params.get("remote"):
        return []
    runs = runs_for_ctx(ctx)
    ops = set([run_util.format_operation(run, nowarn=True) for run in runs])
    return sorted([op for op in ops if op.startswith(incomplete)])


def ac_label(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = runs_for_ctx(ctx)
    labels = set([run.get("label") or "" for run in runs])
    return sorted([_quote_label(l) for l in labels if l and l.startswith(incomplete)])


def _quote_label(l):
    return "\"%s\"" % l


def ac_tag(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    # Reset tags to avoid limiting results based on selected tags.
    ctx.params["tags"] = []
    runs = runs_for_ctx(ctx)
    return [tag for tag in _all_tags_sorted(runs) if tag.startswith(incomplete)]


def _all_tags_sorted(runs):
    tags = set()
    for run in runs:
        tags.update(run.get("tags") or [])
    return sorted(tags)


def ac_digest(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []
    runs = runs_for_ctx(ctx)
    digests = set([run.get("sourcecode_digest") or "" for run in runs])
    return sorted([d for d in digests if d and d.startswith(incomplete)])


def ac_archive(**_kw):
    return click_util.completion_dir() + click_util.completion_filename(ext=["zip"])


def acquire_deprecated_option(fn, opt, param_name):
    """Remove deprecated option from command param fn."""
    for param in fn.__click_params__:
        if opt in param.opts:
            param.opts.remove("-l")
            param.callback = None
        if param.name == param_name:
            if opt not in param.opts:
                param.opts.insert(0, opt)


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
                ("runs",),
                metavar="[RUN...]",
                nargs=-1,
                autocompletion=ac_run,
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
        fn,
        [
            click.Argument(
                ("run",),
                metavar="[RUN]",
                required=False,
                autocompletion=ac_run,
            )
        ],
    )
    return fn


def common_filters(fn):
    """### Filter by Operation

    Runs may be filtered by operation using `--operation`.  A run is
    only included if any part of its full operation name, including
    the package and model name, matches the value.

    Use `--operation` multiple times to include more runs.

    ### Filter by Label

    Use `--label` to only include runs with labels containing a
    specified value. To select runs that do not contain a label,
    specify a dash '-' for `VAL`.

    Use `--label` multiple times to include more runs.

    ### Filter by Tag

    Use `--tag` to only include runs with a specified tag. Tags must
    match completely and are case sensitive.

    Use `--tag` multiple times to include more runs.

    ### Filter by Marked and Unmarked

    Use `--marked` to only include marked runs.

    Use `--unmarked` to only include unmarked runs. This option may
    not be used with `--marked`.

    ### Filter by Run Start Time

    Use `--started` to limit runs to those that have started within a
    specified time range.

    **IMPORTANT:** You must quote RANGE values that contain
    spaces. For example, to filter runs started within the last hour,
    use the option:

        --started 'last hour'

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

    When specifying values like ``minutes`` and ``hours`` the trailing
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

    ### Filter by Source Code Digest

    To show runs for a specific source code digest, use `-g` or
    `--digest` with a complete or partial digest value.

    """
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-Fo", "-o", "--operation", "filter_ops"),
                metavar="VAL",
                help="Filter runs with operations matching `VAL`.",
                multiple=True,
                autocompletion=ac_operation,
                callback=_deprecated("-o", "-Fo"),
            ),
            click.Option(
                ("-Fl", "-l", "--label", "filter_labels"),
                metavar="VAL",
                help="Filter runs with labels matching VAL.",
                multiple=True,
                autocompletion=ac_label,
                callback=_deprecated("-l", "-Fl"),
            ),
            click.Option(
                ("-U", "--unlabeled", "filter_unlabeled"),
                help="Filter only runs without labels (deprecated - use '-Fl -').",
                is_flag=True,
                callback=_deprecated(
                    "-U",
                    "'-Fl -'",
                    "--unlabeled",
                    "'--label -'",
                ),
            ),
            click.Option(
                ("-Ft", "--tag", "filter_tags"),
                metavar="TAG",
                help="Filter runs with TAG.",
                multiple=True,
                autocompletion=ac_tag,
            ),
            click.Option(
                ("-Fc", "--comment", "filter_comments"),
                metavar="VAL",
                help="Filter runs with comments matching VAL.",
                multiple=True,
            ),
            click.Option(
                ("-Fm", "-M", "--marked", "filter_marked"),
                help="Filter only marked runs.",
                is_flag=True,
                callback=_deprecated("-M", "-Fm"),
            ),
            click.Option(
                ("-Fn", "-N", "--unmarked", "filter_unmarked"),
                help="Filter only unmarked runs.",
                is_flag=True,
                callback=_deprecated("-N", "-Fn"),
            ),
            click.Option(
                ("-Fs", "-S", "--started", "filter_started"),
                metavar="RANGE",
                help=(
                    "Filter only runs started within RANGE. See above "
                    "for valid time ranges."
                ),
                callback=_deprecated("-S", "-Fs"),
            ),
            click.Option(
                ("-Fd", "-D", "--digest", "filter_digest"),
                metavar="VAL",
                help=("Filter only runs with a matching source code digest."),
                autocompletion=ac_digest,
                callback=_deprecated("-D", "-Fd"),
            ),
        ],
    )
    return fn


def _deprecated(old_option, new_option, *rest):
    def f(ctx, param, value):
        if old_option in _command_args():
            log.warning(
                "option %s is deprecated and will be removed in version "
                "0.8 - use %s instead",
                old_option,
                new_option,
            )
        if rest:
            # pylint: disable=no-value-for-parameter
            _deprecated(*rest)(ctx, param, value)
        return value

    return f


def _command_args():
    for i, arg in enumerate(sys.argv[1:]):
        if arg[:1] != "-":
            return sys.argv[i + 1 :]
    return []


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
                ("-Sr", "-R", "--running", "status_running"),
                help="Filter only runs that are still running.",
                is_flag=True,
                callback=_deprecated("-R", "-Sr"),
            ),
            click.Option(
                ("-Sc", "-C", "--completed", "status_completed"),
                help="Filter only completed runs.",
                is_flag=True,
                callback=_deprecated("-C", "-Sc"),
            ),
            click.Option(
                ("-Se", "-E", "--error", "status_error"),
                help="Filter only runs that exited with an error.",
                is_flag=True,
                callback=_deprecated("-E", "-Se"),
            ),
            click.Option(
                ("-St", "-T", "--terminated", "status_terminated"),
                help="Filter only runs terminated by the user.",
                is_flag=True,
                callback=_deprecated("-T", "-St"),
            ),
            click.Option(
                ("-Sp", "-P", "--pending", "status_pending"),
                help="Filter only pending runs.",
                is_flag=True,
                callback=_deprecated("-P", "-Sp"),
            ),
            click.Option(
                ("-Ss", "-G", "--staged", "status_staged"),
                help="Filter only staged runs.",
                is_flag=True,
                callback=_deprecated("-G", "-Sg"),
            ),
        ],
    )
    return fn


@click_util.render_doc
def all_filters(fn):
    """
    {{ common_filters }}
    {{ status_filters }}
    """
    click_util.append_params(
        fn,
        [
            common_filters,
            status_filters,
        ],
    )
    return fn


def archive_option(help):
    """### Show Archived Runs

    Use `--archive` to show runs in an archive directory. PATH may be
    a directory or a zip file created using 'guild export'.
    """
    assert isinstance(help, str), "@archive_option must be called with help"

    def wrapper(fn):
        click_util.append_params(
            fn,
            [
                click.Option(
                    ("-A", "--archive"),
                    metavar="PATH",
                    help=help,
                    autocompletion=ac_archive,
                )
            ],
        )
        return fn

    return wrapper
