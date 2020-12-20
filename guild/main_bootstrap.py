# Copyright 2017-2020 TensorHub, Inc.
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

As the bootstrap process is used for every Guild command, it must
execute as quickly as possible.
"""

from __future__ import absolute_import
from __future__ import division

import os
import sys


def main():
    if os.getenv("PROFILE") == "1":
        _profile_main()
    else:
        _main()


def _profile_main():
    import cProfile
    import tempfile

    p = cProfile.Profile()
    sys.stderr.write("Profiling command\n")
    p.enable()
    try:
        _main()
    finally:
        p.disable()
        _, tmp = tempfile.mkstemp(prefix="guild-profile-")
        sys.stderr.write("Writing guild profile stats to %s\n" % tmp)
        p.dump_stats(tmp)
        sys.stderr.write(
            "Use 'python -m pstats %s' or 'snakeviz %s' to view stats\n" % (tmp, tmp)
        )


def _main():
    ensure_external_path()
    import guild.main

    guild.main.main()


def ensure_external_path():
    path = _external_libs_path()
    if path not in sys.path:
        sys.path.insert(0, path)


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
                "https://github.com/guildai/guildai/issues."
            )
        )
        sys.stderr.write("\n")
        sys.exit(1)
    return path


if __name__ == "__main__":
    main()
