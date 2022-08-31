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

import logging
import os
import subprocess
import sys

import yaml

from guild import resource
from guild import resourcedef
from guild import util

log = logging.getLogger("guild")

GPKG_PREFIX = "gpkg."


class Package:
    def __init__(self, ns, name, version):
        self.ns = ns
        self.name = name
        self.version = version


class PackageResource(resource.Resource):
    def _init_resdef(self):
        pkg = yaml.safe_load(self.dist.get_metadata("PACKAGE"))
        if pkg:
            data = pkg.get("resources", {}).get(self.name)
        else:
            data = None
        if not data:
            raise ValueError(f"undefined resource '{self.name}' in {self.dist}")
        fullname = pkg["package"] + "/" + self.name
        resdef = resourcedef.ResourceDef(self.name, data, fullname)
        resdef.dist = self.dist
        return resdef


def create_package(
    package_file,
    clean=False,
    dist_dir=None,
    upload_repo=False,
    sign=False,
    identity=None,
    user=None,
    password=None,
    skip_existing=False,
    comment=None,
    capture_output=False,
):
    # Use a separate OS process as setup assumes it's running as a
    # command line op.
    cmd = [sys.executable, "-um", "guild.package_main"]
    env = {}
    env.update(util.safe_osenv())
    env.update(
        {
            "COMMENT": comment or "",
            "DEBUG": log.getEffectiveLevel() <= logging.DEBUG and "1" or "",
            "DIST_DIR": dist_dir or "",
            "IDENTITY": identity or "",
            "LOG_LEVEL": str(log.getEffectiveLevel()),
            "PACKAGE_FILE": package_file,
            "PASSWORD": password or "",
            "PYTHONPATH": _python_path(),
            "SIGN": "1" if sign else "",
            "SKIP_EXISTING": skip_existing and "1" or "",
            "UPLOAD_REPO": upload_repo or "",
            "USER": user or "",
        }
    )
    if clean:
        env["CLEAN_SETUP"] = "1"
    _apply_twine_env_creds(env)
    cwd = os.path.dirname(package_file)
    if capture_output:
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT
    else:
        stdout = None
        stderr = None
    log.debug("package cmd: %s", cmd)
    log.debug("package env: %s", env)
    log.debug("package cwd: %s", cwd)
    p = subprocess.Popen(cmd, env=env, cwd=cwd, stdout=stdout, stderr=stderr)
    out, _err = p.communicate()
    if p.returncode != 0:
        if capture_output:
            raise SystemExit(p.returncode, out.decode())
        raise SystemExit(p.returncode)
    return out


def _python_path():
    return os.path.pathsep.join([os.path.abspath(path) for path in sys.path])


def _apply_twine_env_creds(env):
    try:
        env["TWINE_USERNAME"] = os.environ["TWINE_USERNAME"]
    except KeyError:
        pass
    try:
        env["TWINE_PASSWORD"] = os.environ["TWINE_PASSWORD"]
    except KeyError:
        pass


def is_gpkg(project_name):
    return project_name.startswith(GPKG_PREFIX)
