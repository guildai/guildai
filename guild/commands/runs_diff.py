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


def _ac_cmd(ctx, **_kw):
    if ctx.params.get("remote"):
        return []
    return click_util.completion_command()


def _ac_path(args, ctx, **_kw):
    ctx = _ctx_for_partial_path_args(args, ctx)
    if ctx.params.get("remote"):
        return []
    dir_base = _diff_dir_base(ctx)
    if not dir_base:
        return []
    return click_util.completion_run_filepath(dir_base)


def _ctx_for_partial_path_args(args, ctx):
    """Return a context for partial path args.

    Click's "resilient parsing" mode for creating a context from args
    appears to not handle the runs args for path completions. To
    workaround we provide a missing path arg.
    """
    args_proxy = []
    found_diff = False
    for val in args:
        if not found_diff:
            found_diff = val == "diff"
            continue
        args_proxy.append(val)
        if val in ("-p", "--path"):
            args_proxy.append("dummy")
    new_ctx = diff_runs.make_context("", args_proxy, resilient_parsing=True)
    new_ctx.parent = ctx.parent
    return new_ctx


def _diff_dir_base(ctx):
    from . import diff_impl

    args = _diff_args_for_ctx(ctx)
    if args.working_dir:
        return args.working_dir
    run = _run_to_diff(args, ctx)
    if not run:
        return []
    if args.working:
        return click_util.completion_safe_apply(
            ctx, diff_impl._find_run_working_dir, [run]
        )
    if args.sourcecode:
        return run.guild_path("sourcecode")
    return run.dir


def _diff_args_for_ctx(ctx):
    args = click_util.Args(**ctx.params)
    args.runs = args.runs or ()
    return args


def _run_to_diff(args, ctx):
    from . import diff_impl
    from . import runs_impl

    def f():
        diff_impl._apply_default_runs(args)
        return runs_impl.one_run(diff_impl.OneRunArgs(args, args.runs[0]), ctx)

    return click_util.completion_safe_apply(ctx, f, [])


def diff_params(fn):
    click_util.append_params(
        fn,
        [
            click.Argument(
                ("runs",),
                metavar="[RUN1 [RUN2]]",
                nargs=-1,
                autocompletion=runs_support.ac_run,
            ),
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
                autocompletion=_ac_path,
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
                ("-c", "--cmd"),
                metavar="CMD",
                help="Command used to diff runs.",
                autocompletion=_ac_cmd,
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
