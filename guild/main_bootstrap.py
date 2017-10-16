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

import imp
import os
import sys

runfile_import_paths = [
    "org_click",
    "org_psutil",
]

def main():
    sys.path[:0] = _external_import_paths()
    _check_requires()
    import guild.main
    guild.main.main()

def _external_import_paths():
    paths = _external_dirs() or _bazel_runfile_dirs()
    assert paths, "count not find external paths"
    return paths

def _external_dirs():
    guild_pkg_dir = os.path.dirname(__file__)
    external_dir = os.path.join(guild_pkg_dir, "external")
    return [external_dir] if os.path.exists(external_dir) else None

def _bazel_runfile_dirs():
    script_dir = os.path.dirname(sys.argv[0])
    runfiles_dir = os.path.join(script_dir, "guild.runfiles")
    return [os.path.join(runfiles_dir, path) for path in runfile_import_paths]

def _check_requires():
    import guild
    for mod_name, req in _sort_reqs(guild.__requires__):
        try:
            imp.find_module(mod_name)
        except ImportError:
            _handle_missing_req(req)

def _sort_reqs(required):
    # Make sure pip is listed first. pip is used to install other
    # required packages and we want to check it first to direct
    # the user to install it before checking other reqs.
    return sorted(
        required,
        key=lambda spec: ("" if spec[0] == "pip"
                          else spec[0].lower()))

def _handle_missing_req(req):
    msg_parts = ["guild: missing required package '%s'\n" % req]
    if req.startswith("pip"):
        msg_parts.append(
            "Refer to https://pip.pypa.io/en/stable/installing "
            "for help installing pip.")
    else:
        msg_parts.append("Try 'pip install %s' to install the package." % req)
    sys.stderr.write("".join(msg_parts))
    sys.stderr.write("\n")
    sys.exit(1)
