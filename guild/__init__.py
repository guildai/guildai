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

from __future__ import absolute_import
from __future__ import division

import os
import subprocess

__version__ = "0.7.2"

__pkgdir__ = os.path.dirname(os.path.dirname(__file__))

__git_commit__ = None
__git_status__ = None


def _try_init_git_attrs():
    try:
        _init_git_commit()
    except (OSError, subprocess.CalledProcessError):
        pass
    else:
        try:
            _init_git_status()
        except (OSError, subprocess.CalledProcessError):
            pass


def _init_git_commit():
    repo = _guild_repo()
    if repo:
        commit = _cmd_out("git --work-tree \"%s\" log -1 --format=\"%%h\"" % repo)
    else:
        commit = None
    globals()["__git_commit__"] = commit


def _guild_repo():
    repo = os.path.dirname(os.path.dirname(__file__))
    if os.path.isdir(os.path.join(repo, ".git")):
        return repo
    return None


def _init_git_status():
    repo = _guild_repo()
    if repo:
        raw = _cmd_out("git -C \"%s\" status -s" % repo)
    else:
        raw = None
    globals()["__git_status__"] = raw.split("\n") if raw else []


def _cmd_out(cmd):
    null = open(os.devnull, "w")
    out = subprocess.check_output(cmd, stderr=null, shell=True)
    return out.decode("utf-8").strip()


def version():
    if __git_commit__:
        workspace_changed_marker = "*" if __git_status__ else ""
        return "%s (dev %s%s)" % (__version__, __git_commit__, workspace_changed_marker)
    else:
        return __version__


def test_version(req):
    from guild import python_util

    return python_util.test_package_version(__version__, req)


_try_init_git_attrs()
