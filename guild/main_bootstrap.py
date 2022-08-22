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
        _fd, tmp = tempfile.mkstemp(prefix="guild-profile-")
        sys.stderr.write(f"Writing guild profile stats to {tmp}\n")
        p.dump_stats(tmp)
        sys.stderr.write(
            f"Use 'python -m pstats {tmp}' or 'snakeviz {tmp}' to view stats\n"
        )


def _main():
    import guild.main

    guild.main.main()


if __name__ == "__main__":
    main()
