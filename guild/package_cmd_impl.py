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

import os

import guild.cmd_support
import guild.package

def create_package(args, ctx):
    project_dir = args.project_location or "."
    package_file = os.path.join(project_dir, "PACKAGE")
    if not os.path.exists(package_file):
        guild.cli.error(
            "a PACKAGE file does not exist in %s\n%s"
            % (guild.cmd_support.project_location_desc(project_dir),
               guild.cmd_support.try_project_location_help(project_dir, ctx)))
    guild.package.create_package(
        package_file,
        dist_dir=args.dist_dir,
        upload=args.upload,
        sign=args.sign,
        identity=args.identity,
        user=args.user,
        password=args.password,
        comment=args.comment)
