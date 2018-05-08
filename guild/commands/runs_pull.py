# Copyright 2017-2018 TensorHub, Inc.
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

def pull_params(fn):
    click_util.append_params(fn, [
        click.Argument(("run",)),
        remote_support.remote_arg,
        click.Option(
            ("-v", "--verbose"),
            help="Show more information.",
            is_flag=True),
        click.Option(
            ("-y", "--yes"),
            help="Do not prompt before copying.",
            is_flag=True),
    ])
    return fn

@click.command("pull")
@pull_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def pull_runs(ctx, args):
    """Copy one or more runs from a remote location.

    `REMOTE` must be define in ``~/.guild/config.yml``. See REMOTES
    below for more information.

    By default Guild will prompt you before copying. If you want to
    apply the changes without being prompted, use the ``--yes``
    option.

    `RUN` must be the complete run ID of the remote run.

    This command does not currently support pulling more than one
    remote run. To list available runs, you must query the remote
    server directly at this time.

    {{ remote_support.remotes }}

    """
    from . import runs_impl
    runs_impl.pull(args, ctx)
