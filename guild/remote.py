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

import re

from guild import config as configlib
from guild import entry_point_util
from guild import opref

_remote_types = entry_point_util.EntryPointResources("guild.remotetypes", "remotetype")


class NoSuchRemote(ValueError):
    pass


class UnsupportedRemoteType(ValueError):
    pass


class ConfigError(ValueError):
    pass


class MissingRequiredConfig(ConfigError):
    pass


class OperationNotSupported(Exception):
    pass


class Down(Exception):
    pass


class OperationError(Exception):
    pass


class InvalidRemoteSpec(ValueError):
    pass


class RemoteForSpecNotImplemented(Exception):
    pass


class RemoteProcessError(Exception):
    def __init__(self, exit_status, cmd, output):
        super(RemoteProcessError, self).__init__(exit_status, cmd, output)
        self.exit_status = exit_status
        self.cmd = cmd
        self.output = output

    @classmethod
    def for_called_process_error(cls, e):
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
        self.dir = self.path = data["run_dir"]
        self.pid = None
        self.status = data.get("status")
        self.remote = None
        self.opref = opref.OpRef.parse(data.get("opref"))
        self.batch_proto = self._init_batch_proto(data)
        self._data = data

    @staticmethod
    def _init_batch_proto(data):
        try:
            proto_data = data["proto-run"]
        except KeyError:
            return None
        else:
            return RunProxy(proto_data)

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


class RemoteType(object):
    def remote_for_config(self, name, config):
        raise NotImplementedError()

    def remote_for_spec(self, spec):
        raise NotImplementedError()


class Remote(object):

    # pylint: disable=unused-argument,no-self-use

    name = None

    def push(self, runs, delete=False):
        raise OperationNotSupported()

    def pull(self, runs, delete=False):
        raise OperationNotSupported()

    def status(self, verbose=False):
        raise OperationNotSupported()

    def start(self):
        raise OperationNotSupported()

    def reinit(self):
        raise OperationNotSupported()

    def stop(self):
        raise OperationNotSupported()

    @staticmethod
    def stop_details():
        return None

    def run_op(self, opspec, flags, restart, no_wait, stage, **opts):
        raise OperationNotSupported()

    def list_runs(self, **opts):
        raise OperationNotSupported()

    def filtered_runs(self, **opts):
        raise OperationNotSupported()

    def one_run(self, run_id_prefix):
        raise OperationNotSupported()

    def watch_run(self, **opts):
        raise OperationNotSupported()

    def delete_runs(self, **opts):
        raise OperationNotSupported()

    def restore_runs(self, **opts):
        raise OperationNotSupported()

    def purge_runs(self, **opts):
        raise OperationNotSupported()

    def label_runs(self, **opts):
        raise OperationNotSupported()

    def tag_runs(self, **opts):
        raise OperationNotSupported()

    def comment_runs(self, **opts):
        raise OperationNotSupported()

    def run_info(self, **opts):
        raise OperationNotSupported()

    def check(self, **opts):
        raise OperationNotSupported()

    def stop_runs(self, **opts):
        raise OperationNotSupported()

    def list_files(self, **opts):
        raise OperationNotSupported()

    def diff_runs(self, **opts):
        raise OperationNotSupported()

    def cat(self, **opts):
        raise OperationNotSupported()


def for_name(name):
    user_config = configlib.user_config()
    remotes = user_config.get("remotes", {})
    try:
        remote = remotes[name]
    except KeyError:
        raise NoSuchRemote(name)
    else:
        remote_config = RemoteConfig(remote)
        remote_type = remote_config["type"]
        try:
            T = _remote_types.one_for_name(remote_type)
        except LookupError:
            raise UnsupportedRemoteType(remote_type)
        else:
            return T.remote_for_config(name, remote_config)


def for_spec(spec):
    m = re.match(r"([\w-]+):(.*)", spec)
    if not m:
        return None
    remote_type, remote_spec = m.groups()
    try:
        T = _remote_types.one_for_name(remote_type)
    except LookupError:
        raise UnsupportedRemoteType(remote_type)
    else:
        try:
            return T.remote_for_spec(remote_spec)
        except NotImplementedError:
            raise RemoteForSpecNotImplemented(remote_type, remote_spec)
