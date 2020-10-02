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


def _ac_tag(ctx, incomplete, **_kw):
    if ctx.params.get("remote"):
        return []

    tags = set()
    ctx.params["runs"] = ctx.args or ["1"]
    for run in runs_support.ac_runs_for_ctx(ctx):
        tags.update(_safe_list(run.get("tags")))
    return [t for t in sorted(tags) if t.startswith(incomplete)]


def _safe_list(x):
    if isinstance(x, list):
        return x
    return []


def tag_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            click.Option(
                ("-a", "--add"),
                metavar="TAG",
                help="Associate TAG with specified runs. May be used multiple times.",
                multiple=True,
            ),
            click.Option(
                ("-d", "--delete"),
                metavar="TAG",
                help="Delete TAG from specified runs. May be used multiple times.",
                multiple=True,
                autocompletion=_ac_tag,
            ),
            click.Option(
                ("-c", "--clear"),
                help="Clear all tags associated with specified runs.",
                is_flag=True,
            ),
            click.Option(
                ("-s", "--sync-labels"),
                help=(
                    "Update run label by adding and deleting corresponding tag parts."
                ),
                is_flag=True,
            ),
            runs_support.all_filters,
            remote_support.remote_option("Tag remote runs."),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before modifying tags.",
                is_flag=True,
            ),
        ],
    )
    return fn


@click.command("tag")
@tag_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def tag_runs(ctx, args):
    """Add or remove run tags.

    Tags may be used to filter runs using the `--tag` option with run
    related commands.

    Use this command to add and remove tags for one or more runs. To
    remove all tags, use `--clear`.

    Note that modifying tags for a run does not modify the run label,
    which may contain tags from when the run was generated. To update
    run labels, use the `label` command.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``1`` is assumed (the most
    recent run).

    {{ runs_support.all_filters }}

    ### Tag Remote Runs

    To tag remote runs, use `--remote`.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl

    runs_impl.tag(args, ctx)
