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

from . import ac_support


def _ac_path_or_package(_ctx, _param, incomplete):
    return _ac_package_names(incomplete) + ac_support.ac_dir(incomplete)


def _ac_package_names(incomplete):
    from . import packages_impl

    return sorted(
        [
            pkg.metadata['Name']
            for pkg in packages_impl.packages(all=False)
            if pkg.metadata['Name'].startswith(incomplete)
        ]
    )


@click.command()
@click.argument("path-or-package", required=False, shell_complete=_ac_path_or_package)
@click.option(
    "--package-description", help="Show the package description.", is_flag=True
)
@click.option("--markdown", help="Show help using Markdown format", is_flag=True)
@click.option(
    "--base-heading-level",
    type=int,
    default=1,
    help="Base heading level for generated markdown (default is 1)",
)
@click.option(
    "--title", default="Guild AI Help", help="Page title used for generating markdown"
)
@click.option(
    "-n", "--no-pager", help="Do not use a pager when showing help.", is_flag=True
)
@click.pass_context
@click_util.use_args
def help(ctx, args):
    """Show help for a path or package.

    By default shows information about the models defined in the
    project.

    To display the description for distributions generated using the
    package command, specify the `--package-description` option.

    """
    from . import help_impl

    help_impl.main(args, ctx)
