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

import os
import random
import threading
import time

import uuid
import yaml

from guild import opref as opreflib
from guild import util
from guild import yaml_util


class Run:

    __properties__ = [
        "id",
        "path",
        "short_id",
        "opref",
        "pid",
        "status",
        "timestamp",
    ]

    def __init__(self, id, path):
        self.id = id
        self.path = path
        self._guild_dir = os.path.join(self.path, ".guild")
        self._opref = None
        self._props = util.PropertyCache(
            [
                ("timestamp", None, self._get_timestamp, 1.0),
                ("pid", None, self._get_pid, 1.0),
            ]
        )

    @property
    def short_id(self):
        return self.id[:8]

    @property
    def dir(self):
        """Alias for path attr."""
        return self.path

    @property
    def opref(self):
        if not self._opref:
            encoded = self._read_opref()
            if encoded:
                try:
                    self._opref = opreflib.OpRef.parse(encoded)
                except opreflib.OpRefError as e:
                    raise opreflib.OpRefError(
                        f"invalid opref for run {self.id!r} ({self.path}): {e}"
                    )
        return self._opref

    def _read_opref(self):
        return util.try_read(self._opref_path())

    def _opref_path(self):
        return self.guild_path("opref")

    def write_opref(self, opref):
        self.write_encoded_opref(str(opref))

    def write_encoded_opref(self, encoded):
        with open(self._opref_path(), "w") as f:
            f.write(encoded)
        self._opref = None

    def reset_opref(self):
        self._opref = None

    @property
    def pid(self):
        return self._props.get("pid")

    def _get_pid(self):
        lockfile = self.guild_path("LOCK")
        try:
            raw = open(lockfile, "r").read(10)
        except (IOError, ValueError):
            return None
        else:
            try:
                return int(raw)
            except ValueError:
                return None

    @property
    def status(self):
        if os.path.exists(self.guild_path("LOCK.remote")):
            return "running"
        if os.path.exists(self.guild_path("PENDING")):
            return "pending"
        if os.path.exists(self.guild_path("STAGED")):
            return "staged"
        return self._local_status()

    @property
    def remote(self):
        remote_lock_path = self.guild_path("LOCK.remote")
        return util.try_read(remote_lock_path, apply=str.strip)

    @property
    def timestamp(self):
        return self._props.get("timestamp")

    def _get_timestamp(self):
        return util.find_apply(
            [
                lambda: self.get("started"),
                lambda: self.get("initialized"),
                lambda: None,
            ]
        )

    @property
    def batch_proto(self):
        proto_dir = self.guild_path("proto")
        proto_opref_path = os.path.join(proto_dir, ".guild", "opref")
        if os.path.exists(proto_opref_path):
            return for_dir(proto_dir)
        return None

    def _local_status(self):
        exit_status = self.get("exit_status")
        if exit_status is not None:
            return _status_for_exit_status(exit_status)
        local_pid = self._get_pid()
        if local_pid is not None and util.pid_exists(local_pid):
            return "running"
        return "error"

    def get(self, name, default=None):
        try:
            val = self[name]
        except KeyError:
            return default
        else:
            return val if val is not None else default

    def attr_names(self):
        return sorted(util.safe_listdir(self._attrs_dir()))

    def has_attr(self, name):
        return os.path.exists(self._attr_path(name))

    def iter_attrs(self):
        for name in self.attr_names():
            try:
                yield name, self[name]
            except KeyError:
                pass

    def __getitem__(self, name):
        try:
            f = open(self._attr_path(name), "r")
        except IOError as e:
            raise KeyError(name) from e
        else:
            return yaml.safe_load(f)

    def _attr_path(self, name):
        return os.path.join(self._attrs_dir(), name)

    def _attrs_dir(self):
        return os.path.join(self._guild_dir, "attrs")

    def __repr__(self):
        return f"<{self.__class__.__module__}.{self.__class__.__name__} '{self.id}'>"

    def init_skel(self):
        util.ensure_dir(self.guild_path("attrs"))
        if not self.has_attr("initialized"):
            self.write_attr("id", self.id)
            self.write_attr("initialized", timestamp())

    def guild_path(self, *subpath):
        if subpath is None:
            return self._guild_dir
        return os.path.join(*((self._guild_dir,) + tuple(subpath)))

    def write_attr(self, name, val, raw=False):
        if not raw:
            val = yaml_util.encode_yaml(val)
        with open(self._attr_path(name), "w") as f:
            f.write(val)
            f.write(os.linesep)
            f.close()

    def del_attr(self, name):
        try:
            os.remove(self._attr_path(name))
        except OSError:
            pass

    def iter_files(self, all_files=False, follow_links=False):
        for root, dirs, files in os.walk(self.path, followlinks=follow_links):
            if not all_files and root == self.path:
                try:
                    dirs.remove(".guild")
                except ValueError:
                    pass
            for name in dirs:
                yield os.path.join(root, name)
            for name in files:
                yield os.path.join(root, name)

    def iter_guild_files(self, subpath):
        guild_path = self.guild_path(subpath)
        if os.path.exists(guild_path):
            for root, dirs, files in os.walk(guild_path):
                rel_root = os.path.relpath(root, guild_path)
                if rel_root == ".":
                    rel_root = ""
                for name in dirs:
                    yield os.path.join(rel_root, name)
                for name in files:
                    yield os.path.join(rel_root, name)


def _status_for_exit_status(exit_status):
    assert exit_status is not None, exit_status
    if exit_status == 0:
        return "completed"
    if exit_status < 0:
        return "terminated"
    return "error"


__last_ts = None
__last_ts_lock = threading.Lock()


def timestamp():
    """Returns an integer use for run timestamps.

    Ensures that subsequent calls return increasing values.
    """
    ts = int(time.time() * 1000000)
    with __last_ts_lock:
        if __last_ts is not None and __last_ts >= ts:
            ts = __last_ts + 1
        globals()["__last_ts"] = ts
    return ts


def timestamp_seconds(ts):
    """Returns seconds float from value generated by `timestamp`."""
    return float(ts / 1000000)


def mkid():
    return uuid.uuid4().hex


def for_dir(run_dir, id=None):
    if not id:
        id = os.path.basename(run_dir)
    return Run(id, run_dir)


def random_seed():
    return random.randint(0, pow(2, 32))
