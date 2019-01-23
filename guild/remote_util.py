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

from guild import config
from guild import remote as remotelib
from guild import util
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
    util.ensure_deleted(lock_file)
    util.ensure_deleted(remote_lock_file)
    if remote_run.status == "running":
        with open(remote_lock_file, "w") as f:
            f.write(remote_name)
    elif remote_run.status == "terminated":
        with open(lock_file, "w") as f:
            f.write("0")

def config_path(path):
    """Returns an absolute path for a config-relative path.

    Variable and user refs are resolved in path.

    If path is None, returns None.
    """
    if path is None:
        return None
    expanded = os.path.expanduser(os.path.expandvars(path))
    config_dir = os.path.dirname(config.user_config_path())
    return os.path.abspath(os.path.join(config_dir, expanded))
