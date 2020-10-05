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
    if ctx.params.get("remote"):
        return []

    # TODO
    return [x for x in ["1", "2", "3"] if x.startswith(incomplete)]


def comment_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            click.Option(
                ("--list",),  # TODO: add -l in 0.8
                help="List comments for specified runs.",
                is_flag=True,
            ),
            click.Option(
                ("-a", "--add"),
                metavar="COMMENT",
                help="Add comment to specified runs.",
            ),
            click.Option(
                ("-d", "--delete"),
                metavar="INDEX",
                help=(
                    "Delete comment at INDEX from specified runs. Use `--list` "
                    "to show available indexes."
                ),
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
                help="User associated with new comments.",
            ),
            click.Option(
                ("-h", "--host"),
                metavar="HOST",
                help="Host associated with new comments.",
            ),
            click.Option(
                ("-s", "--sign"),
                metavar="USER",
                help="Sign the comment as USER.",
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

    To comment remote runs, use `--remote`.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl

    runs_impl.comment(args, ctx)
