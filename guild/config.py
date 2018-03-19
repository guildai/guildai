# Copyright 2017-2018 TensorHub, Inc.
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
import threading

_cwd = None
_cwd_lock = threading.Lock()
_guild_home = None
_log_output = False

def set_cwd(cwd):
    globals()["_cwd"] = cwd

class SetCwd(object):

    def __init__(self, cwd):
        self._cwd = cwd
        self._cwd_orig = None

    def __enter__(self):
        _cwd_lock.acquire()
        self._cwd_orig = cwd()
        set_cwd(self._cwd)

    def __exit__(self, *_args):
        set_cwd(self._cwd_orig)
        _cwd_lock.release()

def set_guild_home(path):
    globals()["_guild_home"] = path

def cwd():
    return _cwd or "."

def guild_home():
    return (
        _guild_home or
        os.getenv("GUILD_HOME") or
        os.path.join(os.path.expanduser("~"), ".guild"))

def set_log_output(flag):
    globals()["_log_output"] = flag

def log_output():
    return _log_output
