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

@click.command()
@click.argument("dir", required=False)
@click.argument("params", metavar="[PARAM=VALUE...]", nargs=-1)
@click.option(
    "-p", "--project", "project_artifact", flag_value="project",
    help="Initialize a new project.")
@click.option(
    "-t", "--template", metavar="TEMPLATE",
    help="Use a template when initializing a project.")
@click.option(
    "--from-package", metavar="PACKAGE",
    help="If initializing a project, use installed `PACKAGE` as a template.")
@click.option(
    "--local-resource-cache", is_flag=True,
    help="Use a local cache when initializing an environment.")
@click.option(
    "--list-templates", is_flag=True,
    help="Show available templates and exit.")
@click.option(
    "--help-template", metavar="TEMPLATE",
    help="Show help for `TEMPLATE` and exit.")
@click.option(
    "-n", "--no-check", is_flag=True,
    help="Don't check the environment after initialization.")
@click.option(
    "-y", "--yes", is_flag=True,
    help="Answer yes to all prompts.")

@click.pass_context
@click_util.use_args

def init(ctx, args):
    """Initialize an environment or project.

    ### Environments

    By default `init` will initialize the default Guild AI environment
    in `DIR`. If `DIR` is not specified, its value is determined by
    whether or not the `init` command is executed in a Python virtual
    environment. If `init` is executed within a virtual environment,
    `DIR` is the value of the `VIRTUAL_ENV` environment variable. If
    `init` is not executed in a virtual environment, `DIR` is the
    user's home directory.

    Environment files are always created in a `.guild` subdirectory of
    `DIR` and no other system files will be modified.

    If `--project` is used, `init` will not initialize a Guild
    environment but will instead initialize a project. See PROJECTS
    below for more information.

    ### Projects

    To initialize a project in `DIR`, use `--project`. If `DIR`
    contains any files that would otherwise be overwritten by `init`,
    the command will exit with an error.

    Projects may be generated using templates. See TEMPLATES below for
    more information.

    Projects may alternatively be generated from installed packages by
    using `--from-package`. When using `--from-package` the use of
    `--project` is implied. If `PACKAGE` is not installed, the command
    will exit with an error.

    ### Templates and parameters

    By default, the template named `default` is used to initialize
    projects. To use a different template, specify it using
    `--template`.

    `--template` may not be used with `--from-package` for
    initializing a project.

    Use `--list-templates` to list available templates.

    Templates support parameters, some of which may be required when
    initializing a project. Use `--help-template` to list template
    parameters.

    Specify parameter values using `PARAM=VALUE` arguments. If the
    first argument, which would otherwise be consideted `DIR`, is in
    the form `PARAM=VALUE`, it will be treated as a paramater and not
    as `DIR.

    ### Shared resource cache

    By default, when initializing an environment outside the user's
    home directory, the new environment will share cached resources
    with the user level environment (i.e. the environment in the
    user's home directory). If you want to completely isolate a new
    environment and ensure that cached resource are not shared, use
    `--local-resource-cache`.

    ### Installing TensorFlow

    When initializing an environment, `init` will check if TensorFlow
    is installed and attempt to install it if it is not. This check
    can be skipped using `--skip-checks`. `init` will prompt before
    installing unless `--yes` is specified.

    ### Examples

    Initialize the default Guild AI environment:

        $ guild init

    Initialize a new default project in the current directory:

        $ guild init --project

    Create a new project from the installed package `guild.mnist`:

        $ guild init --from-package guild.mnist

    """
    from . import init_impl
    init_impl.main(args, ctx)
