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

import guild.config

from guild import opref

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

class OperationError(Exception):
    pass

class RemoteProcessError(Exception):

    def __init__(self, exit_status, cmd, output):
        super(RemoteProcessError, self).__init__(exit_status, cmd, output)
        self.exit_status = exit_status
        self.cmd = cmd
        self.output = output

    @classmethod
    def from_called_process_error(cls, e):
        return cls(e.returncode, e.cmd, e.output)

class RunFailed(Exception):

    def __init__(self, remote_run_dir):
        super(RunFailed, self).__init__(remote_run_dir)
        self.remote_run_dir = remote_run_dir

class RemoteProcessDetached(Exception):
    pass

class RemoteConfig(dict):

    def __getitem__(self, key):
        try:
            return super(RemoteConfig, self).__getitem__(key)
        except KeyError:
            raise MissingRequiredConfig(key)

class RunProxy(object):

    def __init__(self, data):
        self.id = data["id"]
        self.short_id = self.id[:8]
        self.path = data["run_dir"]
        self.pid = None
        self.status = data.get("status")
        self.remote = None
        self._data = data
        self.opref = opref.OpRef.parse(data.get("opref"))

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]

    def attr_names(self):
        return sorted(self._data)

    def has_attr(self, name):
        return name in self._data

    def iter_attrs(self):
        return self._data.items()

    def __repr__(self):
        return "<guild.remote.RunProxy '%s'>" % self.id

    def guild_path(self, _path):
        raise TypeError("guild_path not supported by %s" % self)

class Remote(object):

    name = None

    def push(self, runs, delete=False):
        raise NotImplementedError()

    def pull(self, runs, delete=False):
        raise NotImplementedError()

    def status(self, verbose=False):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def reinit(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    @staticmethod
    def get_stop_details():
        return None

    def run_op(self, opspec, flags, restart, no_wait, **opts):
        raise NotImplementedError()

    def list_runs(self, verbose=False, **filters):
        raise NotImplementedError()

    def filtered_runs(self, **filters):
        raise NotImplementedError()

    def one_run(self, run_id_prefix, attrs):
        raise NotImplementedError()

    def watch_run(self, **opts):
        raise NotImplementedError()

    def delete_runs(self, **opts):
        raise NotImplementedError()

    def restore_runs(self, **opts):
        raise NotImplementedError()

    def purge_runs(self, **opts):
        raise NotImplementedError()

    def label_runs(self, **opts):
        raise NotImplementedError()

    def run_info(self, **opts):
        raise NotImplementedError()

    def check(self, **opts):
        raise NotImplementedError()

    def stop_runs(self, **opts):
        raise NotImplementedError()

def for_name(name):
    user_config = guild.config.user_config()
    remotes = user_config.get("remotes", {})
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
        cls = ssh.SSHRemote
    elif remote_type == "ec2":
        from guild.remotes import ec2
        cls = ec2.EC2Remote
    elif remote_type == "s3":
        from guild.remotes import s3
        cls = s3.S3Remote
    elif remote_type == "tpu":
        from guild.remotes import tpu
        cls = tpu.TPURemote
    elif remote_type == "mock-ssh":
        from guild.remotes import ssh
        cls = ssh.MockSSHRemote
    else:
        raise UnsupportedRemoteType(remote_type)
    remote = cls(name, config)
    return remote
