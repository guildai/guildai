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

"""Bootstraps env for guild.main.

The primary bootstrap task is to configure sys.path with the location
of Guild's external dependencies. This module supports two modes:
distribution and dev.

External dependencies in distribution mode are assumed to be located
in a single `GUILD_PKG_HOME/external` directory where `GUILD_PKG_HOME`
is the `guild` directory within the Guild distribution location.

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

def main():
    sys.path.insert(0, _external_libs_path())
    _check_requires()
    import guild.main
    guild.main.main()

def _external_libs_path():
    guild_pkg_dir = os.path.dirname(__file__)
    path = os.path.abspath(os.path.join(guild_pkg_dir, "external"))
    if not os.path.exists(path):
        import textwrap
        sys.stderr.write("guild: {} does not exist\n".format(path))
        sys.stderr.write(
            textwrap.fill(
                "If you're a Guild developer, run 'python setup.py build' "
                "in the Guild project directory and try again. Otherwise "
                "please report this as a bug at "
                "https://github.com/guildai/guildai/issues."))
        sys.stderr.write("\n")
        sys.exit(1)
    return path

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
        key=lambda spec: ("" if spec[0] == "pip" else spec[0].lower())
    )

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

if __name__ == "__main__":
    main()
