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
    stdout = kw.pop("stdout", None)
    stderr = kw.pop("stderr", None)
    args, cwd, env = _popen_args(*args, **kw)
    p = subprocess.Popen(args, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
    out, err = p.communicate()
    if out is not None:
        out = out.decode()
    if err is not None:
        err = err.decode()
    if p.returncode != 0:
        raise RunError((args, cwd, env), p.returncode, (out, err))
    return out, err


def run_capture_output(*args, **kw):
    args, cwd, env = _popen_args(*args, **kw)
    p = subprocess.Popen(
        args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
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
    tags=None,
    comment=None,
    run_dir=None,
    restart=None,
    start=None,
    stage=None,
    proto=None,
    force_sourcecode=False,
    batch_files=None,
    batch_label=None,
    batch_tags=None,
    batch_comment=None,
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
    stage_trials=False,
    force_flags=False,
    stop_after=None,
    fail_on_trial_error=False,
    print_cmd=False,
    print_trials=False,
    save_trials=None,
    guild_home=None,
    cwd=None,
    quiet=False,
    debug=False,
    test_sourcecode=False,
    gpus=None,
    help_op=False,
):
    from guild import op_util

    cwd = cwd or "."
    flags = flags or {}
    opt_flags = opt_flags or {}
    tags = tags or []
    batch_tags = batch_tags or []
    args = [sys.executable, "-um", "guild.main_bootstrap"]
    if debug:
        args.append("--debug")
    args.extend(["run", "-y"])
    if opspec:
        args.append(opspec)
    if restart:
        args.extend(["--restart", restart])
    # start is a synonym for restart - pass this through as provided.
    if start:
        args.extend(["--start", start])
    if stage:
        args.append("--stage")
    if proto:
        args.extend(["--proto", proto])
    if force_sourcecode:
        args.append("--force-sourcecode")
    if label:
        args.extend(["--label", label])
    for tag in tags:
        args.extend(["--tag", tag])
    if comment:
        args.extend(["--comment", comment])
    if batch_label:
        args.extend(['--batch-label', batch_label])
    for tag in batch_tags:
        args.extend(["--batch-tag", tag])
    if batch_comment:
        args.extend(["--batch-comment", batch_comment])
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
    if stage_trials:
        args.append("--stage-trials")
    if force_flags:
        args.append("--force-flags")
    if stop_after is not None:
        args.extend(["--stop-after", str(stop_after)])
    if fail_on_trial_error:
        args.append("--fail-on-trial-error")
    if quiet:
        args.append("--quiet")
    if test_sourcecode:
        args.append("--test-sourcecode")
    if gpus:
        args.extend(["--gpus", str(gpus)])
    if help_op:
        args.append("--help-op")
    args.extend(op_util.flag_assigns(flags))
    args.extend(["@%s" % path for path in (batch_files or [])])
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
    args.filter_ops = kw.pop("ops", [])
    args.filter_labels = kw.pop("labels", [])
    args.filter_tags = kw.pop("tags", [])
    args.filter_comments = kw.pop("comments", [])
    args.filter_unlabeled = kw.pop("unlabeled", False)
    args.filter_marked = kw.pop("marked", False)
    args.filter_unmarked = kw.pop("unmarked", False)
    args.filter_started = kw.pop("started", None)
    args.filter_digest = kw.pop("digest", None)
    args.status_completed = kw.pop("completed", False)
    args.status_error = kw.pop("error", False)
    args.status_pending = kw.pop("pending", False)
    args.status_running = kw.pop("running", False)
    args.status_staged = kw.pop("staged", False)
    args.status_terminated = kw.pop("terminated", False)


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
        runs=_run_ids(runs), permanent=permanent, remote=False, yes=True
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "runs_delete()")
    with Env(cwd, guild_home):
        runs_impl.delete_runs(args)


def _run_ids(runs):
    if not runs:
        return []
    return [_coerce_run_id(run) for run in runs]


def _coerce_run_id(run):
    if isinstance(run, six.string_types):
        return run
    else:
        return run.id


def runs_label(
    runs=None,
    set=None,
    append=None,
    prepend=None,
    remove=None,
    clear=False,
    cwd=".",
    guild_home=None,
    **kw
):
    from guild import click_util
    from guild.commands import runs_impl
    from guild.commands import runs_label

    args = click_util.Args(
        runs=_run_ids(runs),
        set=set,
        append=append,
        prepend=prepend,
        remove=remove,
        clear=clear,
        remote=False,
        yes=True,
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "runs_label()")
    ctx = runs_label.label_runs.make_context("", [])
    with Env(cwd, guild_home):
        runs_impl.label(args, ctx)


def runs_tag(
    runs=None,
    add=None,
    remove=None,
    clear=False,
    sync_labels=False,
    cwd=".",
    guild_home=None,
    **kw
):
    from guild import click_util
    from guild.commands import runs_impl
    from guild.commands import runs_tag

    args = click_util.Args(
        runs=_run_ids(runs),
        add=_coerce_list(add),
        delete=_coerce_list(remove),
        clear=clear,
        sync_labels=sync_labels,
        remote=False,
        yes=True,
    )
    _apply_runs_filters(kw, args)
    _assert_empty_kw(kw, "runs_tag()")
    ctx = runs_tag.tag_runs.make_context("", [])
    with Env(cwd, guild_home):
        runs_impl.tag(args, ctx)


def _coerce_list(x):
    if isinstance(x, list):
        return x
    elif x is None:
        return []
    else:
        return [x]


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

    args = click_util.Args(runs=_run_ids(runs), clear=clear, yes=True)
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
        runs=_run_ids(runs),
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
        runs=_run_ids(runs),
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
    clean=False,
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
        clean=clean,
        capture_output=True,
    )
    with Env(cwd, guild_home):
        out = package_impl.main(args)
        print(out.decode())


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
