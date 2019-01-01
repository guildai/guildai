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
import subprocess
import sys

import six

# Consider all Guild imports expensive and move to functions

class RunError(Exception):

    def __init__(self, cmd, returncode, out):
        super(RunError, self).__init__(cmd, returncode, out)
        self.cmd_args, self.cmd_cwd, self.cmd_env = cmd
        self.returncode = returncode
        self.out = out

class Env(object):

    def __init__(self, cwd, guild_home=None):
        from guild import config
        from guild.commands import main
        guild_home = guild_home or main.DEFAULT_GUILD_HOME
        self._set_cwd = config.SetCwd(cwd or ".")
        self._set_guild_home = config.SetGuildHome(guild_home)

    def __enter__(self):
        self._set_cwd.__enter__()
        self._set_guild_home.__enter__()

    def __exit__(self, *args):
        self._set_cwd.__exit__(*args)
        self._set_guild_home.__exit__(*args)

def _init_env(cwd, guild_home):
    from guild import config
    from guild.commands import main
    config.set_cwd(cwd)
    config.set_guild_home(guild_home or main.DEFAULT_GUILD_HOME)

def run(spec, cwd=None, flags=None, run_dir=None, guild_home=None,
        extra_env=None):
    import guild
    from guild import op_util
    cwd = cwd or "."
    flags = flags or {}
    args = [
        sys.executable,
        "-um", "guild.main_bootstrap",
        "run", "-y", spec,
    ]
    args.extend([
        "{}={}".format(name, op_util.format_arg_value(val))
        for name, val in flags.items()])
    if run_dir:
        args.extend(["--run-dir", run_dir])
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    _apply_guild_home_env(env, guild_home)
    _apply_python_path_env(env)
    _apply_lang_env(env)
    p = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out_raw, _err = p.communicate()
    out = out_raw.decode().rstrip()
    if p.returncode != 0:
        raise RunError((args, cwd, env), p.returncode, out)
    return out

def _apply_guild_home_env(env, guild_home):
    if guild_home:
        env["GUILD_HOME"] = guild_home

def _apply_python_path_env(env):
    import guild
    guild_path = os.path.abspath(guild.__pkgdir__)
    path = env.get("PYTHONPATH")
    if path:
        path = os.pathsep.join([guild_path, path])
    else:
        path = guild_path
    env["PYTHONPATH"] = path

def _apply_lang_env(env):
    env["LANG"] = os.getenv("LANG", "en_US.UTF-8")

def runs_list(
        ops=None,
        status=None,
        labels=None,
        unlabeled=False,
        all=False,
        deleted=False,
        cwd=".",
        guild_home=None):
    from guild import click_util
    from guild.commands import runs_impl
    status = status or []
    args = click_util.Args(
        ops=(ops or []),
        labels=(labels or []),
        unlabeled=unlabeled,
        running=("running" in status),
        completed=("completed" in status),
        error=("error" in status),
        terminated=("terminated" in status),
        all=all,
        deleted=deleted)
    with Env(cwd, guild_home):
        return runs_impl.filtered_runs(args)

def guild_cmd(command, args, cwd=None, guild_home=None, capture_output=False):
    if isinstance(command, six.string_types):
        command = [command]
    cmd_args = [
        sys.executable,
        "-m", "guild.main_bootstrap",
    ] + command + args
    env = dict(os.environ)
    _apply_guild_home_env(env, guild_home)
    _apply_python_path_env(env)
    _apply_lang_env(env)
    if capture_output:
        return subprocess.check_output(
            cmd_args,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=env)
    else:
        return subprocess.call(
            cmd_args,
            cwd=cwd,
            env=env)
