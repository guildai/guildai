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

import re
import os

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import guildfile
from guild import package

def main(args):
    package_file = os.path.join(config.cwd(), "guild.yml")
    if not os.path.exists(package_file):
        cli.error(
            "%s does not contain a guild.yml file\n"
            "Try specifying a different directory."
            % cmd_impl_support.cwd_desc(config.cwd()))
    _check_upload_config(package_file, args)
    package.create_package(
        package_file,
        dist_dir=args.dist_dir,
        upload_repo=args.upload,
        sign=args.sign,
        identity=args.identity,
        user=args.user,
        password=args.password,
        skip_existing=args.skip_existing,
        comment=args.comment)

def _check_upload_config(package_file, args):
    if not args.upload:
        return
    gf = guildfile.from_file(package_file)
    if not gf.package.author_email:
        cli.error(
            "missing package author-email in %s - cannot upload\n"
            "Specify a valid email for package.author-email and try again."
            % package_file)

    if not _valid_email(gf.package.author_email):
        cli.error(
            "invalid package author-email %r in %s - cannot upload\n"
            "Specify a valid email for package.author-email and try again."
            % (gf.package.author_email, package_file))

def _valid_email(s):
    try:
        m = re.match(r".+?@.+", s)
    except TypeError:
        return False
    else:
        return bool(m)
