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

def set_remote_lock(run_id_or_path, remote_name):
    if os.path.exists(run_id_or_path):
        run_dir = run_id_or_path
    else:
        run_dir = os.path.join(var.runs_dir(), run_id_or_path)
    lock_file = os.path.join(run_dir, ".guild", "LOCK")
    if os.path.exists(lock_file):
        remote_lock_file = os.path.join(run_dir, ".guild", "LOCK.remote")
        with open(remote_lock_file, "w") as f:
            f.write(remote_name)
        os.remove(lock_file)
