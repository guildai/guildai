# Copyright 2017 TensorHub, Inc.
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
@click.option(
    "-p", "--project", "project_location", metavar="LOCATION",
    help="Project location (file system directory) for models.")
# TODO: add system option to show models system wide
@click.option(
    "-v", "--verbose",
    help="Show model details.",
    is_flag=True)

@click.pass_context
@click_util.use_args

def models(ctx, args):
    """Show available models.

    By default Guild will show models defined in the current directory
    (in a MODEL or MODELS file). You may use --project to specify an
    alternative project location.

    To show installed models, use the --installed option. Any location
    specified by --project, will be ignored if --installed is used.
    """
    from . import models_cmd_impl
    models_cmd_impl.main(args, ctx)
