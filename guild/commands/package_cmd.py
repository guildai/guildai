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
    help=("Project location (file system directory) of the "
          "project to package. Defaults to current directory."))
@click.option(
    "-d", "--dist-dir", metavar="DIR",
    help="Directory to create the package distribution in.")
@click.option(
    "--upload",
    help="Upload the package distribution to PyPI after creating it.",
    is_flag=True)
@click.option(
    "-s", "--sign",
    help="Sign a package distribution upload with gpg.",
    is_flag=True)
@click.option("-i", "--identity", help="GPG identity used to sign upload.")
@click.option("-u", "--user", help="PyPI user name for upload.")
@click.option("-p", "--password", help="PyPI password for upload.")
@click.option("-c", "--comment", help="Comment to include with upload.")

@click.pass_context
@click_util.use_args

def package(ctx, args):
    """Create a package for distribution.

    Packages are built from projects that contain a PACKAGE file that
    describes the package to be built.
    """
    from . import package_cmd_impl
    package_cmd_impl.create_package(args, ctx)
