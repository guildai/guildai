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
        stderr=subprocess.STDOUT,
    )
    out, _err = p.communicate()
    out = out.decode()
    if p.returncode != 0:
        raise RunError((args, cwd, env), p.returncode, out)
    return out


def run_quiet(*args, **kw):
    # Use run_capture_output for raising run errors that contain
    # output.
    run_capture_output(*args, **kw)


def _popen_args(
    opspec=None,
    flags=None,
    label=None,
    tag=None,
    run_dir=None,
    restart=None,
    stage=None,
    rerun=None,
    batch_files=None,
    batch_label=None,
    batch_tag=None,
    extra_env=None,
    optimize=False,
    optimizer=None,
    minimize=None,
    maximize=None,
    opt_flags=None,
    max_trials=None,
    random_seed=None,
    debug_sourcecode=None,
    needed=False,
    init_trials=False,
    force_flags=False,
    print_cmd=False,
    print_trials=False,
    save_trials=None,
    guild_home=None,
    cwd=None,
    quiet=False,
    debug=False,
    test_sourcecode=False,
    gpus=None,
):
    from guild import op_util

    cwd = cwd or "."
    flags = flags or {}
    opt_flags = opt_flags or {}
    args = [sys.executable, "-um", "guild.main_bootstrap"]
    if debug:
        args.append("--debug")
    args.extend(["run", "-y"])
    if opspec:
        args.append(opspec)
    if restart:
        args.extend(["--restart", restart])
    if stage:
        args.append("--stage")
    if rerun:
        args.extend(["--rerun", rerun])
    if label:
        args.extend(["--label", label])
    if tag:
        args.extend(["--tag", tag])
    if batch_label:
        args.extend(['--batch-label', batch_label])
    if batch_tag:
        args.extend(["--batch-tag", batch_tag])
    args.extend(op_util.flag_assigns(flags))
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
    for name, val in sorted(opt_flags.items()):
        args.extend(["--opt-flag", op_util.flag_assign(name, val)])
    if max_trials is not None:
        args.extend(["--max-trials", str(max_trials)])
    if random_seed is not None:
        args.extend(["--random-seed", str(random_seed)])
    if debug_sourcecode:
        args.extend(["--debug-sourcecode", debug_sourcecode])
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
    if force_flags:
        args.append("--force-flags")
    if quiet:
        args.append("--quiet")
    if test_sourcecode:
        args.append("--test-sourcecode")
    if gpus:
        args.extend(["--gpus", str(gpus)])
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


def runs_list(all=False, deleted=False, cwd=".", guild_home=None, limit=None, **kw):
    from guild import click_util
    from guild.commands import runs_impl

    args = click_util.Args(all=all, deleted=deleted)
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "runs_list()")
    with Env(cwd, guild_home):
        runs = runs_impl.filtered_runs(args)
        if limit is not None:
            runs = runs[:limit]
        return runs


def _apply_runs_filters(kw, args):
    from guild.commands import runs_impl

    args.ops = kw.pop("ops", [])
    args.labels = kw.pop("labels", [])
    args.unlabeled = kw.pop("unlabeled", False)
    args.marked = kw.pop("marked", False)
    args.unmarked = kw.pop("unmarked", False)
    args.started = kw.pop("started", None)
    args.digest = kw.pop("digest", None)
    for status_attr in runs_impl.FILTERABLE:
        try:
            status_val = kw.pop(status_attr)
        except KeyError:
            pass
        else:
            setattr(args, status_attr, status_val)


def _assert_empty_kw(kw, f):
    try:
        arg = next(iter(kw))
    except StopIteration:
        pass
    else:
        raise TypeError("%s got an unexpected keyword argument '%s'" % (f, arg))


def runs_delete(runs=None, permanent=False, cwd=".", guild_home=None, **kw):
    from guild import click_util
    from guild.commands import runs_impl

    args = click_util.Args(
        runs=(runs or []), permanent=permanent, remote=False, yes=True
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "runs_delete()")
    with Env(cwd, guild_home):
        runs_impl.delete_runs(args)


def guild_cmd(command, args, cwd=None, guild_home=None, capture_output=False):
    if isinstance(command, six.string_types):
        command = [command]
    cmd_args = [sys.executable, "-um", "guild.main_bootstrap",] + command + args
    env = dict(os.environ)
    _apply_guild_home_env(env, guild_home)
    _apply_python_path_env(env)
    _apply_lang_env(env)
    if capture_output:
        return subprocess.check_output(
            cmd_args, stderr=subprocess.STDOUT, cwd=cwd, env=env
        )
    else:
        return subprocess.call(cmd_args, cwd=cwd, env=env)


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


def mark(runs, clear=False, cwd=".", guild_home=None, **kw):
    from guild import click_util
    from guild.commands import runs_impl

    args = click_util.Args(runs=(runs or []), clear=clear, yes=True)
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "mark()")
    with Env(cwd, guild_home):
        runs_impl.mark(args)


def compare(
    runs=None,
    cols=None,
    extra_cols=False,
    all_scalars=False,
    skip_op_cols=False,
    skip_core=False,
    include_batch=False,
    min_col=None,
    max_col=None,
    limit=None,
    cwd=".",
    guild_home=None,
    **kw
):
    from guild import click_util
    from guild.commands import compare_impl

    args = click_util.Args(
        runs=(runs or []),
        extra_cols=extra_cols,
        all_scalars=all_scalars,
        cols=cols,
        skip_op_cols=skip_op_cols,
        skip_core=skip_core,
        include_batch=include_batch,
        min_col=min_col,
        max_col=max_col,
        limit=limit,
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "compare()")
    with Env(cwd, guild_home):
        return compare_impl.get_data(args, format_cells=False)


def publish(
    runs=None,
    dest=None,
    template=None,
    index_template=None,
    files=False,
    all_files=False,
    include_links=False,
    include_batch=False,
    no_md5=False,
    refresh_index=False,
    cwd=".",
    guild_home=None,
    **kw
):
    from guild import click_util
    from guild.commands import publish_impl

    args = click_util.Args(
        runs=(runs or []),
        dest=dest,
        template=template,
        index_template=index_template,
        files=files,
        all_files=all_files,
        include_links=include_links,
        include_batch=include_batch,
        no_md5=no_md5,
        refresh_index=refresh_index,
        yes=True,
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "publish()")
    with Env(cwd, guild_home):
        publish_impl.publish(args, None)


def package(
    dist_dir=None,
    upload=False,
    upload_test=False,
    repo=None,
    sign=False,
    identity=None,
    user=None,
    password=None,
    skip_existing=False,
    comment=None,
    cwd=".",
    guild_home=None,
):
    from guild import click_util
    from guild.commands import package_impl

    args = click_util.Args(
        dist_dir=dist_dir,
        upload=upload,
        upload_test=upload_test,
        repo=repo,
        sign=sign,
        identity=identity,
        user=user,
        password=password,
        skip_existing=skip_existing,
        comment=comment,
    )
    with Env(cwd, guild_home):
        package_impl.main(args)


def select(run=None, min=None, max=None, cwd=".", guild_home=None, **kw):
    from guild import click_util
    from guild.commands import runs_impl

    args = click_util.Args(run=run, min=min, max=max)
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "select()")
    with Env(cwd, guild_home):
        try:
            return runs_impl.select_run(args)
        except SystemExit as e:
            raise ValueError(e)
