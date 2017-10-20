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

import re
import os
import subprocess
import sys

import guild.namespace
import guild.util

DEFAULT_NAMESPACE = "gpkg"

class Package(object):

    def __init__(self, ns, name, version):
        self.ns = ns
        self.name = name
        self.version = version

class NamespaceError(LookupError):
    """Raised if a namespace doesn't exist."""

    def __init__(self, value):
        super(NamespaceError, self).__init__(value)
        self.value = value

def split_name(name):
    """Returns a tuple of namespace and split name.

    Raises NamespaceError if a specified namespace doesn't exist.
    """
    m = re.match("(.+?)/(.+)", name)
    if m:
        return _ns_for_name(m.group(1)), m.group(2)
    else:
        return _ns_for_name(DEFAULT_NAMESPACE), name

def _ns_for_name(name):
    try:
        return guild.namespace.for_name(name)
    except LookupError:
        raise NamespaceError(name)

def apply_namespace(project_name):
    ns = None
    pkg_name = None
    for _, maybe_ns in guild.namespace.iter_namespaces():
        membership, maybe_pkg_name = (
            maybe_ns.is_project_name_member(project_name))
        if membership == guild.namespace.Membership.yes:
            # Match, stop looking
            ns = maybe_ns
            pkg_name = maybe_pkg_name
            break
        elif membership == guild.namespace.Membership.maybe:
            # Possible match, keep looking
            ns = maybe_ns
            pkg_name = maybe_pkg_name
    assert ns, project_name
    assert pkg_name
    return pkg_name

def create_package(package_file, dist_dir=None, upload_repo=False,
                   sign=False, identity=None, user=None, password=None,
                   comment=None):
    # Use a separate OS process as setup assumes it's running as a
    # command line op. We make sure to import package_main lazily here
    # because it incurs various runtime deps that we don't want to
    # load actively.
    import guild.package_main
    cmd = [sys.executable, guild.package_main.__file__]
    env = {}
    env.update(guild.util.safe_osenv())
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
