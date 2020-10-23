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

from . import remote_support
from . import runs_support


def _ac_comment_index(ctx, incomplete, **_kw):
    from . import runs_impl

    if ctx.params.get("remote"):
        return []

    args = click_util.Args(**ctx.params)
    args.runs = ctx.args
    runs = runs_impl.runs_op_selected(args, ctx, runs_impl.LATEST_RUN_ARG)
    indexes = set()
    for run in runs:
        for i in range(len(run.get("comments") or [])):
            indexes.add(str(i + 1))
    return [i for i in sorted(indexes) if i.startswith(incomplete)]


def comment_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            click.Option(
                ("-l", "--list"),
                help="List comments for specified runs.",
                is_flag=True,
            ),
            click.Option(
                ("-a", "--add"),
                metavar="COMMENT",
                help="Add comment to specified runs.",
            ),
            click.Option(
                ("-e", "--edit"),
                help=(
                    "Use an editor to type a comment. Enabled by default if "
                    "COMMENT is not specified using --add."
                ),
                is_flag=True,
            ),
            click.Option(
                ("-d", "--delete"),
                metavar="INDEX",
                help=(
                    "Delete comment at INDEX from specified runs. Use `--list` "
                    "to show available indexes."
                ),
                type=click.INT,
                autocompletion=_ac_comment_index,
            ),
            click.Option(
                ("-c", "--clear"),
                help="Clear all comments associated with specified runs.",
                is_flag=True,
            ),
            click.Option(
                ("-u", "--user"),
                metavar="USER",
                help=(
                    "User associated with new comments. May include host "
                    "as USER@HOST. By default the current user is used."
                ),
            ),
            runs_support.all_filters,
            remote_support.remote_option("Apply comments to remote runs."),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before modifying comments.",
                is_flag=True,
            ),
        ],
    )
    runs_support.acquire_deprecated_option(fn, "-l", "list")
    return fn


@click.command("comment")
@comment_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def comment_runs(ctx, args):
    """Add or remove run comments.

    By default Guild opens the default text editor to add a new
    comment to the specified runs.

    To list runs, use `--list`.

    To add a comment without using an editor, use `--add`.

    To delete a comment, use `--delete` with the comment index shown
    using `--list`.

    To delete all comments associated with specified runs, use `--clear`.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``1`` is assumed (the most
    recent run).

    {{ runs_support.all_filters }}

    ### Comment Remote Runs

    To apply the comment command to remote runs, use `--remote`. When
    using `--remote` you must explicitly provide comments when adding
    using `-a, --add`. The `--edit` option is not supported with
    `--remote`.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl

    runs_impl.comment(args, ctx)
