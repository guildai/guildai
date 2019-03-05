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

    def __init__(self, cmd, returncode, output=None):
        super(RunError, self).__init__(cmd, returncode, output)
        self.cmd_args, self.cmd_cwd, self.cmd_env = cmd
        self.returncode = returncode
        self.output = output

class Env(object):

    def __init__(self, cwd, guild_home=None):
        from guild import config
        guild_home = guild_home or config.guild_home()
        self._set_cwd = config.SetCwd(cwd or ".")
        self._set_guild_home = config.SetGuildHome(guild_home)

    def __enter__(self):
        self._set_cwd.__enter__()
        self._set_guild_home.__enter__()

    def __exit__(self, *args):
        self._set_cwd.__exit__(*args)
        self._set_guild_home.__exit__(*args)

def run(*args, **kw):
    args, cwd, env = _popen_args(*args, **kw)
    p = subprocess.Popen(args, cwd=cwd, env=env)
    returncode = p.wait()
    if returncode != 0:
        raise RunError((args, cwd, env), returncode)

def run_capture_output(*args, **kw):
    args, cwd, env = _popen_args(*args, **kw)
    p = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out, _err = p.communicate()
    out = out.decode()
    if p.returncode != 0:
        raise RunError((args, cwd, env), p.returncode, out)
    return out

def _popen_args(
        spec=None,
        cwd=None,
        flags=None,
        batch_files=None,
        run_dir=None,
        restart=None,
        label=None,
        guild_home=None,
        extra_env=None,
        optimize=False,
        optimizer=None,
        minimize=None,
        maximize=None,
        opt_flags=None,
        max_trials=None,
        random_seed=None,
        needed=False,
        init_trials=False,
        print_cmd=False,
        print_trials=False,
        save_trials=None,
        quiet=False):
    from guild import op_util
    cwd = cwd or "."
    flags = flags or {}
    opt_flags = opt_flags or {}
    args = [
        sys.executable,
        "-um", "guild.main_bootstrap",
        "run", "-y"
    ]
    if spec:
        args.append(spec)
    if restart:
        args.extend(["--restart", restart])
    if label:
        args.extend(['--label', label])
    args.extend([
        "{}={}".format(name, op_util.format_flag_val(val))
        for name, val in flags.items()])
    args.extend(["@%s" % path for path in (batch_files or [])])
    if run_dir:
        args.extend(["--run-dir", run_dir])
    if optimize:
        args.append("--optimize")
    if optimizer:
        args.extend(["--optimizer", optimizer])
    if minimize:
        args.extend(["--minimize", minimize])
    if maximize:
        args.extend(["--maximize", maximize])
    for name, val in opt_flags.items():
        args.extend([
            "--opt-flag",
            "{}={}".format(name, op_util.format_flag_val(val))
        ])
    if max_trials is not None:
        args.extend(["--max-trials", str(max_trials)])
    if random_seed is not None:
        args.extend(["--random-seed", str(random_seed)])
    if needed:
        args.append("--needed")
    if print_cmd:
        args.append("--print-cmd")
    if print_trials:
        args.append("--print-trials")
    if save_trials:
        args.extend(["--save-trials", save_trials])
    if init_trials:
        args.append("--init-trials")
    if quiet:
        args.append("--quiet")
    env = dict(os.environ)
    env["NO_IMPORT_FLAGS_PROGRESS"] = "1"
    if extra_env:
        env.update(extra_env)
    _apply_guild_home_env(env, guild_home)
    _apply_python_path_env(env)
    _apply_lang_env(env)
    return args, cwd, env

def _apply_guild_home_env(env, guild_home):
    if guild_home:
        env["GUILD_HOME"] = guild_home
    else:
        try:
            env["GUILD_HOME"] = os.environ["GUILD_HOME"]
        except KeyError:
            pass

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
        marked=False,
        unmarked=False,
        cwd=".",
        guild_home=None):
    from guild import click_util
    from guild.commands import runs_impl
    status = status or []
    args = click_util.Args(
        ops=(ops or []),
        labels=(labels or []),
        unlabeled=unlabeled,
        all=all,
        deleted=deleted,
        marked=marked,
        unmarked=unmarked)
    _apply_status_filters(status, args)
    with Env(cwd, guild_home):
        return runs_impl.filtered_runs(args)

def _apply_status_filters(status, args):
    from guild.commands import runs_impl
    for val in status:
        if val not in runs_impl.FILTERABLE:
            raise ValueError("unsupportd status %r" % val)
        setattr(args, val, True)

def runs_delete(runs=None, cwd=".", guild_home=None):
    from guild import click_util
    from guild.commands import runs_delete
    from guild.commands import runs_impl
    runs = runs or []
    args = runs + ["--yes"]
    ctx = runs_delete.delete_runs.make_context("", args)
    with Env(cwd, guild_home):
        runs_impl.delete_runs(click_util.Args(**ctx.params), ctx)

def guild_cmd(command, args, cwd=None, guild_home=None, capture_output=False):
    if isinstance(command, six.string_types):
        command = [command]
    cmd_args = [
        sys.executable,
        "-um", "guild.main_bootstrap",
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

class NoCurrentRun(Exception):
    pass

def current_run():
    """Returns an instance of guild.run.Run for the current run.

    The current run directory must be specified with the RUN_DIR
    environment variable. If this variable is not defined, raised
    NoCurrentRun.

    """
    import guild.run
    path = os.getenv("RUN_DIR")
    if not path:
        raise NoCurrentRun()
    return guild.run.Run(os.getenv("RUN_ID"), path)

def mark(run, clear=False, cwd=".", guild_home=None):
    from guild import click_util
    from guild.commands import mark
    from guild.commands import runs_impl
    args = [run, "--yes"]
    if clear:
        args.append("--clear")
    ctx = mark.mark.make_context("", args)
    args = click_util.Args(**ctx.params)
    with Env(cwd, guild_home):
        return runs_impl.mark(args, ctx)

def compare(
        runs=None,
        columns=None,
        skip_op_cols=False,
        skip_core=False,
        cwd=".", guild_home=None):
    from guild import click_util
    from guild.commands import compare
    from guild.commands import compare_impl
    args = list(runs or ())
    if columns:
        args.extend(["--columns", columns])
    if skip_op_cols:
        args.append("--skip-op-cols")
    if skip_core:
        args.append("--skip-core")
    ctx = compare.compare.make_context("", args)
    args = click_util.Args(**ctx.params)
    with Env(cwd, guild_home):
        return compare_impl._get_data(args, format_cells=False)
