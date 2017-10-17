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

"""Bootstraps env for guild.main.

The primary bootstrap task is to configure sys.path with the location
of Guild's external dependencies. This module supports two modes:
distribution and dev.

External dependencies in distribution mode are assumed to be located
in a single `GUILD_PKG_HOME/external` directory where `GUILD_PKG_HOME`
is the `guild` directory within the Guild distribution location.

External dependencies in dev mode are assumed be in multiple
directories, one for each dependency, under
`SCRIPT_DIR/guild.runfiles` where `SCRIPT_DIR` is the directory
containing `sys.argv[0]` (i.e. the Guild executable script).

This module confirms that it can find each of the modules listed in
guild.__requires__ but does not load the modules. The module exits
with an error and a user facing message for any missing requirements.

As the bootstrap process is used for every Guild command, it must
execute as quickly as possible.
"""

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
    paths = _external_distribution() or _external_dev()
    assert paths, "count not find external paths"
    return paths

def _external_distribution():
    guild_pkg_dir = os.path.dirname(__file__)
    external_dir = os.path.join(guild_pkg_dir, "external")
    return [external_dir] if os.path.exists(external_dir) else None

def _external_dev():
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
