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

import logging
import os
import sys

from guild import config
from guild import log as loglib
from guild import remote as remotelib
from guild import subprocess
from guild import util
from guild import var

log = logging.getLogger("guild")


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


def subprocess_call(cmd, extra_env=None, quiet=False, allowed_returncodes=(0,)):
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
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
    if returncode not in allowed_returncodes:
        for line in buffer:
            sys.stderr.write(line)
        raise SystemExit(
            "error running %s - see above for details" % cmd[0], returncode
        )
    return returncode


def init_env(env_config):
    return _legal_env(_env_for_config(env_config))


def _env_for_config(env_config):
    if isinstance(env_config, dict):
        return env_config
    elif isinstance(env_config, str):
        return _env_from_file(env_config)
    elif env_config is None:
        return {}
    else:
        log.warning("invalid value for remote env %r - ignoring", env_config)
        return {}


def _legal_env(env):
    return {name: str(val) for name, val in env.items() if val}


def _env_from_file(path):
    if path.lower().endswith(".gpg"):
        env_str = _try_read_gpg(path)
    else:
        env_str = util.try_read(path)
    if not env_str:
        log.warning("cannot read remote env from %s - ignorning", path)
        return {}
    return _decode_env(env_str)


def _try_read_gpg(path):
    path = os.path.expanduser(path)
    cmd = _gpg_cmd() + [path]
    log.debug("gpg cmd: %s", cmd)
    try:
        p = subprocess.Popen(
            cmd, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError as e:
        log.error("cannot decode %s with command '%s' (%s)", path, " ".join(cmd), e)
    else:
        out, err = p.communicate()
        if p.returncode != 0:
            log.error(err.decode(errors="replace").strip())
            return None
        return out.decode(errors="replace")


def _gpg_cmd():
    gpg_env = os.getenv("GPG_CMD")
    if gpg_env:
        return util.shlex_split(gpg_env)
    return ["gpg", "-d"]


def _decode_env(s):
    return dict([_split_env_line(line) for line in s.split("\n")])


def _split_env_line(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        parts.append("")
    return _strip_export(parts[0]), parts[1]


def _strip_export(s):
    s = s.strip()
    if s.startswith("export "):
        s = s[7:]
    return s


def remote_activity(msg, *args):
    """Log remote activity.

    Used to report time consuming work that would otherwise not show
    user feedback. E.g. use when synchronizing meta data.
    """
    log.info(loglib.dim(msg), *args)
