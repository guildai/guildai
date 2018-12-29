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
from . import remote_support
from . import runs_support

def push_params(fn):
    click_util.append_params(fn, [
        runs_support.runs_arg,
        remote_support.remote_arg,
        runs_support.op_and_label_filters,
        runs_support.status_filters,
        click.Option(
            ("-n", "--delete",),
            help="Delete remote files missing locally.",
            is_flag=True),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before copying.",
            is_flag=True),
    ])
    return fn

@click.command("push")
@push_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def push_runs(ctx, args):
    """Copy one or more runs to a remote location.

    `REMOTE` must be define in ``~/.guild/config.yml``. See REMOTES
    below for more information.

    By default Guild will prompt you before copying. If you want to
    apply the changes without being prompted, use the ``--yes``
    option.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``:`` is assumed (all runs
    are selected).

    {{ runs_support.op_and_label_filters }}

    {{ runs_support.status_filters }}

    {{ remote_support.remotes }}

    """
    from . import runs_impl
    runs_impl.push(args, ctx)
