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
import subprocess
import sys

import guild

class RunError(Exception):

    def __init__(self, cmd_args, returncode, out, err):
        super(RunError, self).__init__(cmd_args, returncode, out, err)
        self.cmd_args = cmd_args
        self.returncode = returncode
        self.out = out
        self.err = err

def run(spec, cwd=None, flags=None, run_dir=None):
    cwd = cwd or "."
    flags = flags or []
    args = [
        sys.executable,
        "-um", "guild.main_bootstrap",
        "run", "-y", spec,
    ]
    args.extend(["{}={}".format(name, val) for name, val in flags])
    if run_dir:
        args.extend(["--run-dir", run_dir])
    guild_home = os.path.abspath(guild.__pkgdir__)
    env = {
        "PYTHONPATH": guild_home,
        "LANG": os.getenv("LANG", "en_US.UTF-8"),
    }
    p = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RunError(args, p.returncode, out, err)
    return out.rstrip(), err.rstrip()
