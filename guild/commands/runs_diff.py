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


def diff_params(fn):
    click_util.append_params(
        fn,
        [
            click.Argument(("runs",), metavar="[RUN1 [RUN2]]", nargs=-1),
            click.Option(("-O", "--output"), is_flag=True, help="Diff run output."),
            click.Option(
                ("-s", "--sourcecode"), is_flag=True, help="Diff run source code."
            ),
            click.Option(("-e", "--env"), is_flag=True, help="Diff run environment."),
            click.Option(("-f", "--flags"), is_flag=True, help="Diff run flags."),
            click.Option(
                ("-a", "--attrs"),
                is_flag=True,
                help=(
                    "Diff all run attributes; if specified other "
                    "attribute options are ignored."
                ),
            ),
            click.Option(("-d", "--deps"), is_flag=True, help="Diff run dependencies."),
            click.Option(
                ("-p", "--path"),
                metavar="PATH",
                multiple=True,
                help="Diff specified path; may be used more than once.",
            ),
            click.Option(
                ("-w", "--working"),
                is_flag=True,
                help="Diff run sourcecode to the associated working directory.",
            ),
            click.Option(
                ("-W", "--working-dir"),
                metavar="PATH",
                help="Diff run sourcecode to the specified directory.",
            ),
            click.Option(
                ("-c", "--cmd"), metavar="CMD", help="Command used to diff runs."
            ),
            runs_support.all_filters,
            remote_support.remote_option("Diff remote runs."),
        ],
    )
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

    If `RUN1` or `RUN2` is specified, both must be specified. An
    exception to this is when `--working` or `--working-dir` is
    specified, in which case `RUN2` cannot be specified (see below).

    {{ runs_support.all_filters }}

    ### Diff Sourcecode

    Use `--soucecode` to diff source code between two runs. Use
    `--working` to diff one run and its associated soure code working
    directory. The working directory is run's Guild file sourcecode
    root directory. Use `--working-dir` to specify an alternative
    source code directory. Both `--working` and `--working-dir` imply
    `--sourcecode`. When either `--working` or `--working-dir` are
    used, `RUN2` cannot also be specified.

    ### Diff Command

    By default the ``diff`` program is used to diff run details. An
    alternative default command may be specified in
    ``~/.guild/config.yml`` using the ``command`` attribute of the
    ``diff`` section.

    To use a specific diff program with the command, use `--cmd`.

    ### Diff Remote Runs

    To diff remote runs, use `--remote`. Note that any command
    specified by `--cmd` must be available on the remote and must show
    differences over standard output.

    {{ remote_support.remote_option }}

    """
    from . import diff_impl

    diff_impl.main(args, ctx)
