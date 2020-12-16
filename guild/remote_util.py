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

import hashlib
import os
import re
import sys

from guild import config
from guild import remote as remotelib
from guild import subprocess
from guild import util
from guild import var


def require_env(name):
    if name not in os.environ:
        raise remotelib.OperationError(
            "missing required %s environment variable" % name
        )


def set_remote_lock(remote_run, remote_name, runs_dir=None):
    assert isinstance(remote_run, remotelib.RunProxy), remote_run
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


def subprocess_call(cmd, env=None, quiet=False):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    buffer = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if quiet:
            buffer.append(line.decode())
        else:
            sys.stderr.write(line.decode())
    returncode = p.wait()
    if returncode != 0:
        for line in buffer:
            sys.stderr.write(line)
        raise SystemExit(
            "error running %s - see above for details" % cmd[0], returncode
        )


def local_meta_dir(remote_name, key):
    base_dir = var.remote_dir(_safe_filename(remote_name))
    key_hash = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(base_dir, "meta", key_hash)


def _safe_filename(s):
    if not s:
        return s
    return re.sub(r"\W+", "-", s).strip("-") or "-"
