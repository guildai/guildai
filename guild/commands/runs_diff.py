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

def diff_params(fn):
    click_util.append_params(fn, [
        click.Argument(("runs",), metavar="[RUN1 RUN2]", nargs=-1),
        click.Option(
            ("-O", "--output"),
            is_flag=True,
            help="Diff run output."),
        click.Option(
            ("-s", "--source"),
            is_flag=True,
            help="Diff run source."),
        click.Option(
            ("-e", "--env"),
            is_flag=True,
            help="Diff run environment."),
        click.Option(
            ("-g", "--flags"),
            is_flag=True,
            help="Diff run flags."),
        click.Option(
            ("-a", "--attrs"),
            is_flag=True,
            help=(
                "Diff all run attributes; if specified other "
                "attribute options are ignored.")),
        click.Option(
            ("-d", "--deps"),
            is_flag=True,
            help="Diff run dependencies."),
        click.Option(
            ("-p", "--path"),
            metavar="PATH",
            multiple=True,
            help="Diff specified path; may be used more than once."),
        click.Option(
            ("-c", "--cmd"),
            metavar="CMD",
            help="Command used to diff runs."),
        runs_support.op_and_label_filters,
        runs_support.status_filters,
    ])
    return fn

@click.command("diff")
@diff_params

@click.pass_context
@click_util.use_args
@click_util.render_doc

def diff_runs(ctx, args):
    """Diff two runs.

    If `RUN1` and `RUN2` are omitted, the latest two filtered runs are
    diffed. See FILTERING topics below for details on filtering runs
    to diff.

    If `RUN1` or `RUN2` is specified, both must be specified.

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}

    ### Diff command

    By default the ``diff`` program is used to diff run details. An
    alternative default command may be specified in
    ``~/.guild/config.yml`` using the ``command`` attribute of the
    ``diff`` section.

    To use a specific diff program with the command, use `--cmd`.

    """
    from . import diff_impl
    diff_impl.main(args, ctx)
