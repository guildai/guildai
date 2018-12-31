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

import logging
import os
import re
import subprocess
import sys

import guild.log
import guild.run

log = None # intialized in _init_logging

def main():
    _init_logging()
    _run_steps()

def _init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild.op_steps")

def _run_steps():
    run = _init_run()
    steps = _init_steps(run)
    if not steps:
        log.warning("no steps defined for run %s", run.id)
        return
    for step in steps:
        _run_step(step, run)

def _init_run():
    run_id, run_dir = _run_environ()
    return guild.run.Run(run_id, run_dir)

def _run_environ():
    try:
        return os.environ["RUN_ID"], os.environ["RUN_DIR"]
    except KeyError as e:
        _internal_error("missing required env %s" % e.args[0])

def _init_steps(run):
    return run.get("steps") or []

def _run_step(step, parent_run):
    step_run_dir = _init_step_run(parent_run)
    cmd = _init_step_cmd(step, step_run_dir)
    _link_to_step_run(step, step_run_dir, parent_run.path)
    env = dict(os.environ)
    env["NO_WARN_RUNDIR"] = "1"
    subprocess.call(cmd, env=env, cwd=os.getenv("CMD_DIR"))

def _init_step_run(parent_run):
    """Returns the run dir for a step run.

    Directory is based on a new, unique run ID but is not created.
    """
    run_id = guild.run.mkid()
    runs_dir = os.path.dirname(parent_run.path)
    return os.path.join(runs_dir, run_id)

def _init_step_cmd(step, step_run_dir):
    guild_exe = os.getenv("GUILD_SCRIPT") or "guild"
    op_spec = _step_op_spec(step)
    flag_args = _step_flag_args(step)
    base_args = [
        guild_exe, "run", "-y",
        "--run-dir", step_run_dir,
        op_spec]
    return base_args + flag_args

def _step_op_spec(step):
    assert isinstance(step, str)
    return step

def _step_flag_args(_step):
    return []

def _link_to_step_run(step, step_run_dir, parent_run_dir):
    link_name = _step_link_name(step)
    link_path_base = os.path.join(parent_run_dir, link_name)
    link_path = _ensure_unique_link(link_path_base)
    os.symlink(step_run_dir, link_path)

def _step_link_name(step):
    assert isinstance(step, str)
    return re.sub(r"[ :/\\]", "_", step)

def _ensure_unique_link(path_base):
    v = 2
    path = path_base
    while True:
        assert v < 1e6
        if not os.path.exists(path):
            return path
        path = "%s_%i" % (path_base, v)
        v += 1

def _internal_error(msg):
    sys.stderr.write("guild.op_main: %s\n" % msg)
    sys.exit(2)

if __name__ == "__main__":
    main()
