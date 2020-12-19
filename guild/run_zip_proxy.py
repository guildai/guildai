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
import zipfile

import yaml

from guild import run as runlib


class RunZipProxy(runlib.Run):
    def __init__(self, id, src, prefix=None):
        prefix = prefix or id
        path = src + ":" + prefix
        self.prefix = prefix
        self.zip_src = src
        super(RunZipProxy, self).__init__(id, path)

    def _read_opref(self):
        encoded = _try_zip_entry(self.zip_src, self.prefix, ".guild/opref")
        if encoded:
            return encoded.decode()
        return None

    def __getitem__(self, name):
        try:
            encoded = _zip_entry(self.zip_src, self.prefix, ".guild/attrs", name)
        except KeyError:
            raise KeyError(name)
        else:
            return yaml.safe_load(encoded)

    @property
    def batch_proto(self):
        proto_path = _zip_path(self.prefix, ".guild/proto", "")
        try:
            _zip_entry(self.zip_src, proto_path)
        except KeyError:
            return None
        else:
            return RunZipProxy("proto", self.zip_src, proto_path[:-1])


def _try_zip_entry(src, prefix, path):
    try:
        return _zip_entry(src, prefix, path)
    except KeyError:
        return None


def _zip_entry(src, *path):
    with zipfile.ZipFile(src, "r") as zf:
        return zf.read(_zip_path(*path))


def _zip_path(*parts):
    return "/".join(parts)


def all_runs(archive):
    runs = {}
    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            _ensure_run(name, archive, runs)
    return list(runs.values())


def _ensure_run(name, archive, runs):
    run_id = name.split("/", 1)[0]
    try:
        return runs[run_id]
    except KeyError:
        runs[run_id] = run = RunZipProxy(run_id, archive)
        return run


def copy_run(src, run_id, dest):
    dest_parent = os.path.dirname(dest)
    prefix = run_id + "/"
    with zipfile.ZipFile(src, "r") as zf:
        for name in zf.namelist():
            if name.startswith(prefix):
                zf.extract(name, dest_parent)
