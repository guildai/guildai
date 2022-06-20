# Copyright 2017-2022 RStudio, PBC
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

import click

from guild import click_util

from . import runs_merge


@click.command("merge")
@runs_merge.merge_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def main(ctx, args):
    """Provides merge support.

    Use '--preview' to generate JSON output describing a merge.

    This command does not prompt for user input. If '--yes' is not
    specified, the command fails with an error on a merge attemp.
    """
    from guild.util import StderrCapture
    from .merge_impl import main as merge_main

    _check_merge_without_yes(args, ctx)

    with StderrCapture() as out:
        try:
            merge_main(args, ctx)
        except SystemExit as e:
            _handle_exit(e, out)
        else:
            _handle_exit(SystemExit(0), out)


def _check_merge_without_yes(args, ctx):
    from guild import cli

    if not args.preview and not args.yes:
        cli.error(
            "--yes must be specified for this command when --preview is not used\n"
            f"Try '{ctx.command_path} --help' for more information."
        )


def _handle_exit(e, out):
    from guild.main import system_exit_params

    msg, code = system_exit_params(e)
    print(msg, code, out.get_value())
