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

def publish_params(fn):
    click_util.append_params(fn, [
        runs_support.runs_arg,
        click.Option(
            ("-d", "--dest"),
            metavar="DIR",
            help="Destination to publish runs."),
        click.Option(
            ("-t", "--template"),
            metavar="VAL",
            help="Template used to publish runs."),
        click.Option(
            ("--refresh-index",),
            help="Refresh runs index without publishing anything.",
            is_flag=True),
        runs_support.op_and_label_filters,
        runs_support.status_filters,
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before publishing.",
            is_flag=True),
    ])
    return fn

@click.command("publish")
@publish_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def publish_runs(ctx, args):
    """Publish one or more runs.

    By default, runs are published to 'published-runs'
    subdirectory. To specify a different location, use `--dest`.

    Each run operation may define an alternative destination using the
    `publish` attribute in the Guild file. This value will be used for
    any associated runs unless `--dest` is provided, in which case the
    user provided value is used.

    After publishing runs to destination `DIR`, Guild updates the runs
    index `README.md` in `DIR`. To refresh the index without
    publishing anything, use `--refresh-index`.

    """
    from . import runs_impl
    runs_impl.publish(args, ctx)
