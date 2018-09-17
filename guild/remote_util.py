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

from guild import remote as remotelib
from guild import var

def require_env(name):
    if name not in os.environ:
        raise remotelib.OperationError(
            "missing required %s environment variable"
            % name)

def set_remote_lock(remote_run, remote_name, runs_dir=None):
    runs_dir = runs_dir or var.runs_dir()
    local_run_dir = os.path.join(runs_dir, remote_run.id)
    lock_file = os.path.join(local_run_dir, ".guild", "LOCK")
    remote_lock_file = os.path.join(local_run_dir, ".guild", "LOCK.remote")
    _ensure_deleted(lock_file)
    _ensure_deleted(remote_lock_file)
    if remote_run.status == "running":
        with open(remote_lock_file, "w") as f:
            f.write(remote_name)
    elif remote_run.status == "terminated":
        with open(lock_file, "w") as f:
            f.write("0")

def _ensure_deleted(path):
    try:
        os.remove(path)
    except (IOError, OSError) as e:
        if e.errno != 2:
            raise
