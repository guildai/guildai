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

import guild.config

class NoSuchRemote(ValueError):
    pass

class UnsupportedRemoteType(ValueError):
    pass

class MissingRequiredConfig(ValueError):
    pass

class OperationNotSupported(Exception):
    pass

class Down(Exception):
    pass

class RemoteConfig(dict):

    def __getitem__(self, key):
        try:
            return super(RemoteConfig, self).__getitem__(key)
        except KeyError:
            raise MissingRequiredConfig(key)

class Remote(object):

    name = None

    def push(self, runs, verbose=False):
        raise NotImplementedError()

    def push_dest(self):
        raise NotImplementedError()

    def pull(self, run_ids, verbose=False):
        raise NotImplementedError()

    def pull_all(self, verbose=False):
        raise NotImplementedError()

    def pull_src(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

def for_name(name):
    remotes = guild.config.user_config().get("remotes", {})
    try:
        remote = remotes[name]
    except KeyError:
        raise NoSuchRemote(name)
    else:
        remote_config = RemoteConfig(remote)
        remote_type = remote_config["type"]
        return _for_type(remote_type, name, remote_config)

def _for_type(remote_type, name, config):
    # Hard-code for now. If this goes anywhere we can make it an
    # entry-point or use the plugin framework.
    if remote_type == "ssh":
        from guild.remotes import ssh
        remote = ssh.SSHRemote(config)
        remote.name = name
        return remote
    else:
        raise UnsupportedRemoteType(remote_type)
