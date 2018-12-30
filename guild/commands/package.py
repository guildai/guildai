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

@click.command()
@click.option(
    "-d", "--dist-dir", metavar="DIR",
    help="Directory to create the package distribution in.")
@click.option(
    "--upload", "upload",
    help="Upload to PyPI after creating the package.",
    flag_value="https://upload.pypi.org/legacy/")
@click.option(
    "--upload-test", "upload",
    help="Upload to the PyPI test site after creating the package.",
    flag_value="https://test.pypi.org/legacy/")
@click.option(
    "--repo", "upload", metavar="REPO",
    help="Upload to `REPO` after creating the package.")
@click.option(
    "-s", "--sign",
    help="Sign a package distribution upload with gpg.",
    is_flag=True)
@click.option(
    "-i", "--identity", metavar="IDENTITY",
    help="GPG identity used to sign upload.")
@click.option(
    "-u", "--user", metavar="USERNAME",
    help="PyPI user name for upload.")
@click.option(
    "-p", "--password", metavar="PASSWORD",
    help="PyPI password for upload.")
@click.option(
    "-e", "--skip-existing", is_flag=True,
    help="Don't upload if package already exists.")
@click.option(
    "-c", "--comment", metavar="COMMENT",
    help="Comment to include with upload.")

@click_util.use_args

def package(args):
    """Create a package for distribution.

    Packages are built from projects that contain guildfile with a
    package definition, which describes the package to be built.

    You may upload the generated package distribution to a PyPI
    repository by using the `--upload` option or to the PyPI test site
    by using `--upload-test`.

    You may upload to an alternative repository using
    `--upload-repo`. `REPO` may be a URL or the name of a section in
    `~/.pypirc`. For more information on the `.pypirc` file, see:

    https://docs.python.org/2/distutils/packageindex.html#pypirc

    """
    from . import package_impl
    package_impl.main(args)
