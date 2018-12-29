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
from . import runs_support

def export_params(fn):
    click_util.append_params(fn, [
        runs_support.runs_arg,
        click.Argument(("location",)),
        click.Option(
            ("-m", "--move"),
            help="Move exported runs rather than copy.",
            is_flag=True),
        click.Option(
            ("--copy-resources",),
            help="Copy resources for each exported run.",
            is_flag=True),
        runs_support.op_and_label_filters,
        runs_support.status_filters,
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before exporting.",
            is_flag=True),
    ])
    return fn

@click.command("export")
@export_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def export_runs(ctx, args):
    """Export one or more runs.

    `LOCATION` must be a writeable directory.

    By default, runs are copied to `LOCATION`. Use `--move` to move
    them instead.

    By default, resources are NOT copied with each exported run, but
    their links are maintained. To copy resources, use
    `--copy-resources`.

    **WARNING**: Use `--copy-resources` with care as each exported run
    will contain a separate copy of each resource!

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}

    """

    from . import runs_impl
    runs_impl.export(args, ctx)
