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
import sys

EXTERNAL_PATHS = [
    "org_click",
    "org_html5lib",
    "org_mozilla_bleach",
    "org_psutil",
    "org_pythonhosted_markdown",
    "org_tensorflow_tensorboard",
    "protobuf/python",
]

def main():
    sys.path[:0] = _external_import_paths()
    _check_requires()
    import guild.main
    guild.main.main()

def _external_import_paths():
    external_root = _external_root()
    return [
        _external_import_path(path, external_root)
        for path in EXTERNAL_PATHS
    ]

def _external_root():
    root = _package_external_dir() or _bazel_runfiles_dir()
    assert root, "could not find external root"
    return root

def _package_external_dir():
    guild_pkg_dir = os.path.dirname(__file__)
    external_dir = os.path.join(guild_pkg_dir, "external")
    return external_dir if os.path.exists(external_dir) else None

def _bazel_runfiles_dir():
    script_dir = os.path.dirname(sys.argv[0])
    runfiles_dir = os.path.join(script_dir, "guild.runfiles")
    return runfiles_dir if os.path.exists(runfiles_dir) else None

def _external_import_path(path, root):
    if isinstance(path, tuple):
        if sys.version_info[0] == 2:
            path = path[0]
        else:
            path = path[1]
    return os.path.join(root, path)

def _check_requires():
    import pkg_resources
    import guild
    for pkg in _sort_reqs(guild.__requires__):
        try:
            pkg_resources.require(pkg)
        except pkg_resources.DistributionNotFound as e:
            _handle_missing_req(e.req)

def _sort_reqs(required):
    # Make sure pip is listed first. pip is used to install other
    # required packages and we want to check it first to direct
    # the user to install it before checking other reqs.
    return sorted(required, key=lambda x: "" if x == "pip" else x.lower())

def _handle_missing_req(req):
    msg_parts = ["guild: missing required package '%s'\n" % req]
    if req.project_name == "pip":
        msg_parts.append(
            "Refer to https://pip.pypa.io/en/stable/installing "
            "for help installing pip.")
    else:
        msg_parts.append("Try 'pip install %s' to install the package." % req)
    sys.stderr.write("".join(msg_parts))
    sys.stderr.write("\n")
    sys.exit(1)
