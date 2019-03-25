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

from __future__ import absolute_import
from __future__ import division

import os
import subprocess

__version__ = "0.6.0"

__requires__ = [
    # (<required module>, <distutils package req>)
    ("pip", "pip"),
    ("yaml", "PyYAML"),
    ("setuptools", "setuptools"),
    ("six", "six"),
    ("tabview", "tabview"),
    ("twine", "twine"),
    ("werkzeug", "Werkzeug"),
    ("whoosh", "Whoosh"),
]

__pkgdir__ = os.path.dirname(os.path.dirname(__file__))

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
    commit = _git_cmd("git -C \"%(repo)s\" log -1 --oneline | cut -d' ' -f1")
    globals()["__git_commit__"] = commit

def _init_git_status():
    raw = _git_cmd("git -C \"%(repo)s\" status -s")
    globals()["__git_status__"] = raw.split("\n") if raw else []

def _git_cmd(cmd, **kw):
    repo = os.path.dirname(__file__)
    cmd = cmd % dict(repo=repo, **kw)
    null = open(os.devnull, "w")
    out = subprocess.check_output(cmd, stderr=null, shell=True)
    return out.decode("utf-8").strip()

def version():
    git_commit = globals().get("__git_commit__")
    if git_commit:
        git_status = globals().get("__git_status__", [])
        workspace_changed_marker = "*" if git_status else ""
        return "%s (dev %s%s)" % (__version__, git_commit,
                                 workspace_changed_marker)
    else:
        return __version__

_try_init_git_attrs()
