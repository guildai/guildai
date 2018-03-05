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

import os

from guild import cli
from guild import cmd_impl_support
from guild import config
from guild import package

def create_package(args):
    package_file = os.path.join(config.cwd(), "guild.yml")
    if not os.path.exists(package_file):
        cli.error(
            "%s does not contain a guild.yml file\n"
            "Try specifying a different directory."
            % cmd_impl_support.cwd_desc(config.cwd()))
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
