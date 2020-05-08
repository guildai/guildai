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

import re
import os

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import guildfile
from guild import package


def main(args):
    if not os.path.exists(config.cwd()):
        cli.error(
            "%s does not exist\n"
            "Try specifying a different directory."
            % cmd_impl_support.cwd_desc(config.cwd())
        )
    package_file = guildfile.guildfile_path()
    if not os.path.exists(package_file):
        cli.error(
            "%s does not contain a guild.yml file\n"
            "A guild.yml file is required when creating a package. Create one "
            "in this directory first or try specifying a different directory."
            % cmd_impl_support.cwd_desc(config.cwd())
        )
    if args.upload:
        _check_upload_support(package_file)
    out = package.create_package(
        package_file,
        clean=args.clean,
        dist_dir=args.dist_dir,
        upload_repo=args.upload,
        sign=args.sign,
        identity=args.identity,
        user=args.user,
        password=args.password,
        skip_existing=args.skip_existing,
        comment=args.comment,
        capture_output=args.capture_output,
    )
    return out


def _check_upload_support(package_file):
    _check_twine_installed()
    _check_upload_config(package_file)


def _check_twine_installed():
    try:
        import twine as _
    except ImportError:
        cli.error(
            "Twine is required to upload packages. Install it by running "
            "'pip install twine'."
        )


def _check_upload_config(package_file):
    gf = guildfile.for_file(package_file)
    if not gf.package.author_email:
        cli.error(
            "missing package author-email in %s - cannot upload\n"
            "Specify a valid email for package.author-email and try again."
            % package_file
        )

    if not _valid_email(gf.package.author_email):
        cli.error(
            "invalid package author-email %r in %s - cannot upload\n"
            "Specify a valid email for package.author-email and try again."
            % (gf.package.author_email, package_file)
        )


def _valid_email(s):
    try:
        m = re.match(r".+?@.+", s)
    except TypeError:
        return False
    else:
        return bool(m)
