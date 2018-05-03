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

import logging
import os
import threading

import yaml

log = logging.getLogger("guild")

_cwd = None
_cwd_lock = threading.Lock()
_guild_home = None
_log_output = False
_user_config = None

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

class _Config(object):

    def __init__(self, path):
        self.path = path
        self._parsed = None
        self._mtime = 0

    def read(self):
        if self._parsed is None or self._path_mtime() > self._mtime:
            self._parsed = self._parse()
            self._mtime = self._path_mtime()
        return self._parsed

    def _path_mtime(self):
        try:
            return os.path.getmtime(self.path)
        except IOError:
            return 0

    def _parse(self):
        try:
            f = open(self.path, "r")
        except IOError as e:
            log.warning("cannot read user config in %s: %s", self.path, e)
        else:
            try:
                return yaml.load(f)
            except Exception as e:
                log.warning("error loading user config in %s: %s", self.path, e)
        return {}

def user_config():
    path = _user_config_path()
    config = _user_config
    if config is None or config.path != path:
        config = _Config(path)
        globals()["_user_config"] = config
    return config.read()

def _user_config_path():
    return os.path.join(os.path.expanduser("~"), ".guild", "config.yml")
