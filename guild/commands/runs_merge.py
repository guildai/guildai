# Copyright 2017-2023 Posit Software, PBC
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


def merge_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.run_arg,
            runs_support.all_filters,
            click.Option(
                ("-t", "--target-dir"),
                help=(
                    "Directory to merge run files to (required if project directory "
                    "cannot be determined for the run)."
                ),
                metavar="DIR",
            ),
            click.Option(
                ("-s", "--sourcecode"),
                help=(
                    "Only copy run source code. Implies use of `--skip-deps`. "
                    "Cannot be used with `--skip-sourcecode`."
                ),
                is_flag=True,
            ),
            click.Option(
                ("-a", "--all"),
                help=(
                    "Copy all run files. May be used with `--skip-sourcecode`, "
                    "`--skip-deps`, and `--exclude` to copy all but the "
                    "skipped/excluded files."
                ),
                is_flag=True,
            ),
            click.Option(
                ("-S", "--skip-sourcecode"),
                help="Don't copy run source code.",
                is_flag=True,
            ),
            click.Option(
                ("-D", "--skip-deps"),
                help="Don't copy project-local dependencies.",
                is_flag=True,
            ),
            click.Option(
                ("-x", "--exclude"),
                help="Exclude a file or pattern (may be used multiple times).",
                metavar="PATTERN",
                multiple=True,
            ),
            click.Option(
                ("-S", "--no-summary"),
                help="Don't generate a run summary.",
                is_flag=True,
            ),
            click.Option(
                ("n", "--summary-name"),
                help=(
                    "Name used for the run summary. Use '${run_id}' in the name to "
                    "include the run ID."
                ),
                metavar="NAME",
            ),
            click.Option(
                ("-p", "--preview"),
                help="Show what would happen on a merge.",
                is_flag=True,
            ),
            click.Option(
                ("-y", "--yes"),
                help="Don't prompt before copying files.",
                is_flag=True,
            ),
            click.Option(
                ("--replace",),
                help=(
                    "Allow replacement of existing files. Cannot be used with "
                    "--no-replace"
                ),
                is_flag=True,
            ),
            click.Option(
                ("--no-replace",),
                help=(
                    "Fail if any target file would be replaced, even if that file "
                    "is committed to the project VCS. Cannot be used with `--replace`."
                ),
                is_flag=True,
            ),
        ],
    )
    return fn


@click.command("merge")
@merge_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def merge_runs(ctx, args):
    """Copy run files to a project directory.

    By default, Guild copies run files into the current directory. To
    copy files to a different directory, use ``--target-dir DIR``.

    Guild checks that the run originated from the current directory
    before copying files. If the run is associated with a project from
    a different directory, or is from a package, Guild exits with an
    error message. In this case, use `--target-dir` to override the
    check with an explicit path.

    The command fails if any file would be replaced, unless a) the
    `--replace` option is specified or b) the replaced file is
    committed to the project VCS and unchanged. To prevent replacement
    even when a file is committed to VCS and unchanged, specify
    `--no-replace`.
    """
    from . import merge_impl

    merge_impl.main(args, ctx)
