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

import os
import subprocess
import sys

from guild import namespace
from guild import resource
from guild import resourcedef
from guild import util
from guild import yaml

class Package(object):

    def __init__(self, ns, name, version):
        self.ns = ns
        self.name = name
        self.version = version

class PackageResource(resource.Resource):

    def _init_resdef(self):
        pkg = yaml.safe_load(self.dist.get_metadata("PACKAGE"))
        data = pkg.get("resources", {}).get(self.name)
        if not data:
            raise ValueError(
                "undefined resource '%s' in %s"
                % self.name, self.dist)
        fullname = pkg["name"] + "/" + self.name
        return resourcedef.ResourceDef(self.name, data, fullname)

def create_package(package_file, dist_dir=None, upload_repo=False,
                   sign=False, identity=None, user=None, password=None,
                   comment=None):
    # Use a separate OS process as setup assumes it's running as a
    # command line op.
    cmd = [sys.executable, "-um", "guild.package_main"]
    env = {}
    env.update(util.safe_osenv())
    env.update({
        "PYTHONPATH": os.path.pathsep.join(sys.path),
        "PACKAGE_FILE": package_file,
        "DIST_DIR": dist_dir or "",
        "UPLOAD_REPO": upload_repo or "",
        "SIGN": "1" if sign else "",
        "IDENTITY": identity or "",
        "USER": user or "",
        "PASSWORD": password or "",
        "COMMENT": comment or "",
    })
    p = subprocess.Popen(cmd, env=env)
    exit_code = p.wait()
    if exit_code != 0:
        raise SystemExit(exit_code)

def is_gpkg(project_name):
    ns = namespace.for_name("gpkg")
    return ns.project_name_membership(project_name) == namespace.Membership.yes
