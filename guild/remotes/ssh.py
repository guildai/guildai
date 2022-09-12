# Copyright 2017-2022 RStudio, PBC
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

import glob
import json
import os
import logging
import re
import shutil
import subprocess
import sys

from guild import click_util
from guild import config
from guild import op_util
from guild import remote as remotelib
from guild import remote_util
from guild import run as runlib
from guild import util
from guild import var

from . import ssh_util

log = logging.getLogger("guild.remotes.ssh")

DEFAULT_DIFF_CMD = "diff -ru"


class SSHRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return SSHRemote(name, config)

    def remote_for_spec(self, spec):
        user, host, port, path = _parse_spec(spec)
        config = remotelib.RemoteConfig(
            {
                "host": host,
                "port": port,
                "user": user,
                "venv-path": path,
            }
        )
        return SSHRemote(spec, config)


def _parse_spec(spec):
    m = re.match(r"(?:(\w+)@)?([^/:]+)(?::(\d+))?(?::(.+))?$", spec)
    if not m:
        raise remotelib.InvalidRemoteSpec(
            f"invalid ssh spec '{spec}' - "
            "expected format [USER@]HOST[:PORT][/ENV_PATH]"
        )
    return (
        m.group(1),
        m.group(2),
        int(m.group(3)) if m.group(3) else None,
        m.group(4),
    )


class SSHRemote(remotelib.Remote):
    def __init__(self, name, config):
        self.name = name
        self._host = config["host"]
        self.port = config.get("port")
        self.user = config.get("user")
        self.private_key = config.get("private-key")
        self.connect_timeout = config.get("connect-timeout")
        self.venv_path = config.get("venv-path") or config.get("guild-env")
        self.conda_env = config.get("conda-env")
        self.guild_home = self._init_guild_home(config)
        self.venv_activate = config.get("venv-activate")
        self.use_prerelease = config.get("use-prerelease", False)
        self.init = config.get("init")
        self.proxy = config.get("proxy")

    def _init_guild_home(self, config):
        return util.find_apply(
            [
                self._explicit_guild_home,
                self._guild_home_from_conda_env,
                self._guild_home_from_venv,
                self._default_guild_home,
            ],
            config,
        )

    @staticmethod
    def _explicit_guild_home(config):
        return config.get("guild-home")

    @staticmethod
    def _guild_home_from_conda_env(config):
        val = config.get("conda-env")
        if val is None:
            return None
        if "/" not in val:
            raise remotelib.ConfigError(
                f"cannot determine Guild home from conda-env {val!r} - "
                "specify a path for conda-env or specify guild-home"
            )
        return util.strip_trailing_sep(val) + "/.guild"

    @staticmethod
    def _guild_home_from_venv(config):
        val = config.get("venv-path") or config.get("guild-env")
        if val is None:
            return None
        return util.strip_trailing_sep(val) + "/.guild"

    @staticmethod
    def _default_guild_home(_config):
        return ".guild"

    @property
    def host(self):
        return self._host

    def push(self, runs, delete=False):
        for run in runs:
            self._push_run(run, delete)

    def _push_run(self, run, delete):
        src = run.path + "/"
        dest_path = f"{self.guild_home}/runs/{run.id}/"
        dest = ssh_util.format_rsync_host_path(self.host, dest_path, self.user)
        cmd = (
            ["rsync"]
            + self._rsync_path_mkdir_opts(dest_path)
            + self._push_rsync_opts(delete)
            + [src, dest]
        )
        cmd.extend(
            ssh_util.rsync_ssh_opts(
                remote_util.config_path(self.private_key),
                self.connect_timeout,
                self.port,
                self.proxy,
            )
        )
        log.info("Copying %s", run.id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    @staticmethod
    def _rsync_path_mkdir_opts(dest):
        dest_dir = os.path.dirname(dest)
        return ["--rsync-path", f"mkdir -p {dest_dir} && rsync"]

    @staticmethod
    def _push_rsync_opts(delete):
        opts = ["-al"]
        if delete:
            opts.append("--delete")
        if log.getEffectiveLevel() <= logging.DEBUG:
            opts.append("-vvv")
        else:
            opts.append("-v")
        return opts

    def pull(self, runs, delete=False):
        for run in runs:
            self._pull_run(run, delete)

    def _pull_run(self, run, delete):
        src_path = f"{self.guild_home}/runs/{run.id}/"
        src = ssh_util.format_rsync_host_path(self.host, src_path, self.user)
        dest = os.path.join(var.runs_dir(), run.id + "/")
        util.ensure_dir(os.path.dirname(dest))
        cmd = ["rsync"] + self._pull_rsync_opts(delete) + [src, dest]
        cmd.extend(
            ssh_util.rsync_ssh_opts(
                remote_util.config_path(self.private_key),
                self.connect_timeout,
                self.port,
                self.proxy,
            )
        )
        log.info("Copying %s", run.id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)
        remote_util.set_remote_lock(run, self.name)

    @staticmethod
    def _pull_rsync_opts(delete):
        opts = [
            "-al",
            "--inplace",
            "--exclude",
            ".guild/job-packages",
            "--exclude",
            ".guild/LOCK*",
        ]
        if delete:
            opts.append("--delete")
        if log.getEffectiveLevel() <= logging.DEBUG:
            opts.append("-vvv")
        else:
            opts.append("-v")
        return opts

    def reinit(self):
        if not self.init:
            raise remotelib.OperationNotSupported("init is not defined for this remote")
        self._ssh_cmd(self.init)

    def status(self, verbose=False):
        ssh_util.ssh_ping(
            self.host,
            user=self.user,
            private_key=self.private_key,
            verbose=verbose,
            connect_timeout=self.connect_timeout,
            port=self.port,
            proxy=self.proxy,
        )
        sys.stdout.write(f"{self.name} ({self.host}) is available\n")

    def run_op(self, opspec, flags, restart, no_wait, stage, **opts):
        with util.TempDir(prefix="guild-remote-stage-") as tmp:
            if not restart:
                op_src = _op_src(opspec)
                if op_src:
                    _build_package(op_src, tmp.path)
            remote_run_dir = self._init_remote_run(tmp.path, opspec, restart)
        run_id = os.path.basename(remote_run_dir)
        self._start_op(remote_run_dir, opspec, restart, flags, run_id, stage, **opts)
        if stage:
            log.info("%s staged as on %s as %s", opspec, self.name, run_id)
            log.info(
                "To start the operation, use 'guild run -r %s --start %s'",
                self.name,
                run_id,
            )
        if no_wait or stage:
            return run_id
        try:
            self._watch_started_op(remote_run_dir)
        except KeyboardInterrupt as e:
            raise remotelib.RemoteProcessDetached(run_id) from e
        else:
            return run_id

    def _init_remote_run(self, package_dist_dir, opspec, restart):
        remote_run_dir = self._init_remote_run_dir(opspec, restart)
        if not restart and self._contains_whl(package_dist_dir):
            self._copy_package_dist(package_dist_dir, remote_run_dir)
            self._install_job_package(remote_run_dir)
        return remote_run_dir

    def _init_remote_run_dir(self, opspec, restart_run_id):
        if restart_run_id:
            return self._init_remote_restart_run_dir(restart_run_id)
        return self._init_remote_new_run_dir(opspec)

    @staticmethod
    def _contains_whl(dir):
        return bool(glob.glob(os.path.join(dir, "*.whl")))

    def _init_remote_restart_run_dir(self, remote_run_id):
        run_dir = os.path.join(self.guild_home, "runs", remote_run_id)
        cmd = (
            "set -e; "
            "test ! -e {run_dir}/.guild/LOCK || exit 3; "
            "touch {run_dir}/.guild/PENDING; "
            "echo \"$(date +%s)000000\" > {run_dir}/.guild/attrs/started".format(
                run_dir=run_dir
            )
        )
        log.info("Initializing remote run for restart")
        try:
            self._ssh_cmd(cmd)
        except remotelib.RemoteProcessError as e:
            if e.exit_status == 3:
                raise remotelib.OperationError("running", remote_run_id)
            raise
        else:
            return run_dir

    def _ssh_cmd(self, cmd):
        ssh_util.ssh_cmd(
            self.host,
            [cmd],
            user=self.user,
            private_key=remote_util.config_path(self.private_key),
            connect_timeout=self.connect_timeout,
            port=self.port,
            proxy=self.proxy,
        )

    def _init_remote_new_run_dir(self, opspec):
        run_id = runlib.mkid()
        run_dir = os.path.join(self.guild_home, "runs", run_id)
        cmd = (
            "set -e; "
            "mkdir -p {run_dir}/.guild; "
            "touch {run_dir}/.guild/PENDING; "
            "mkdir {run_dir}/.guild/attrs; "
            "echo 'pending:? ? ? {opspec}' > {run_dir}/.guild/opref; "
            "echo \"$(date +%s)000000\" > {run_dir}/.guild/attrs/started; "
            "mkdir {run_dir}/.guild/job-packages".format(run_dir=run_dir, opspec=opspec)
        )
        log.info("Initializing remote run")
        self._ssh_cmd(cmd)
        return run_dir

    def _copy_package_dist(self, package_dist_dir, remote_run_dir):
        src = package_dist_dir + "/"
        host_dest = f"{remote_run_dir}/.guild/job-packages/"
        log.info("Copying package")
        ssh_util.rsync_copy_to(
            src,
            self.host,
            host_dest,
            user=self.user,
            private_key=remote_util.config_path(self.private_key),
            connect_timeout=self.connect_timeout,
            port=self.port,
            proxy=self.proxy,
        )

    def _install_job_package(self, remote_run_dir):
        cmd_lines = []
        cmd_lines.extend(self._env_activate_cmd_lines())
        cmd_lines.extend(
            [
                f"cd {remote_run_dir}/.guild/job-packages",
                f"pip install{self._pre_flag()} --upgrade *.whl --target .",
            ]
        )
        cmd = "; ".join(cmd_lines)
        log.info("Installing package and its dependencies")
        self._ssh_cmd(cmd)

    def _pre_flag(self):
        if self.use_prerelease:
            return " --pre"
        return ""

    def _start_op(self, remote_run_dir, opspec, restart, flags, run_id, stage, **opts):
        pidfile = f"{remote_run_dir}/.guild/JOB" if not stage else None
        python_path = f"$(realpath {remote_run_dir})/.guild/job-packages:$PYTHONPATH"
        args = _run_args(
            opspec=opspec if not restart else None,
            op_flags=flags,
            run_dir=_noquote(remote_run_dir) if not restart else None,
            start=restart,
            stage=stage,
            pidfile=_noquote(pidfile),
            quiet=True,
            yes=True,
            **opts,
        )
        env = {
            "PYTHONPATH": python_path,
            "NO_STAGED_MSG": "1",
            "NO_IMPORT_FLAGS_PROGRESS": "1",
            "NO_WARN_RUNDIR": "1",
        }
        if not stage:
            log.info("Starting %s on %s as %s", opspec, self.name, run_id)
        self._guild_cmd("run", args, env)

    def _watch_started_op(self, remote_run_dir):
        cmd_lines = ["set -e"]
        cmd_lines.extend(self._env_activate_cmd_lines())
        cmd_lines.append(
            f"NO_WATCHING_MSG=1 guild watch --pid {remote_run_dir}/.guild/JOB"
        )
        cmd = "; ".join(cmd_lines)
        log.debug("watching remote run")
        try:
            self._ssh_cmd(cmd)
        except remotelib.RemoteProcessError as e:
            if e.exit_status != 2:
                raise
            raise remotelib.RunFailed(remote_run_dir)

    def list_runs(self, **opts):
        args = _list_runs_filter_args(**opts)
        self._guild_cmd("runs list", args)

    def filtered_runs(self, **filters):
        remote_util.remote_activity("Getting run info on %s", self.name)
        opts = _filtered_runs_filter_opts(**filters)
        out = self._guild_cmd_output("runs list", opts)
        if not out:
            data = []
        else:
            data = json.loads(out.decode())
            assert isinstance(data, list), (data, self.name)
        return [remotelib.RunProxy(run_data) for run_data in data]

    def _ssh_output(self, cmd):
        return ssh_util.ssh_output(
            self.host,
            [cmd],
            user=self.user,
            private_key=remote_util.config_path(self.private_key),
            connect_timeout=self.connect_timeout,
            port=self.port,
            proxy=self.proxy,
        )

    def _env_activate_cmd_lines(self):
        return util.find_apply(
            [
                self._explicit_venv_activate,
                self._conda_env_activate,
                self._default_venv_activate,
            ]
        )

    def _explicit_venv_activate(self):
        if self.venv_activate:
            return [self.venv_activate]
        return None

    def _conda_env_activate(self):
        if self.conda_env:
            return [
                f"source {self.conda_env}/etc/profile.d/conda.sh > /dev/null 2>&1 || "
                f"source {self.conda_env}/../../etc/profile.d/conda.sh > /dev/null 2>&1",
                f"conda activate '{self.conda_env}'",
            ]
        return None

    def _default_venv_activate(self):
        if self.venv_path:
            return [f"source {self.venv_path}/bin/activate"]
        return []

    def one_run(self, run_id_prefix):
        out = self._guild_cmd_output(
            "runs info", [run_id_prefix, "--private-attrs", "--json"]
        )
        remote_util.remote_activity("Resolving run on %s", self.name)
        run_data = self._run_data_for_json(out)
        return remotelib.RunProxy(run_data)

    @staticmethod
    def _run_data_for_json(s):
        return json.loads(s.decode())

    def watch_run(self, **opts):
        self._guild_cmd("watch", _watch_run_args(**opts))

    def _guild_cmd(self, name, args, env=None):
        cmd = self._init_guild_cmd(name, args, env)
        self._ssh_cmd(cmd)

    def _init_guild_cmd(self, name, args, env):
        cmd_lines = ["set -e"]
        cmd_lines.extend(self._env_activate_cmd_lines())
        cmd_lines.extend(self._set_columns())
        assert self.guild_home is not None
        cmd_lines.append(f"export GUILD_HOME={self.guild_home}")
        if env:
            cmd_lines.extend(self._cmd_env(env))
        quoted_args = [_quote_arg(arg) for arg in args]
        cmd_lines.append(f"guild {name} {_join_args(quoted_args)}")
        return "; ".join(cmd_lines)

    def _guild_cmd_output(self, name, args, env=None):
        cmd = self._init_guild_cmd(name, args, env)
        return self._ssh_output(cmd)

    @staticmethod
    def _set_columns():
        w, _h = shutil.get_terminal_size()
        return [f"export COLUMNS={w}"]

    @staticmethod
    def _cmd_env(env):
        return [f"export {name}={val}" for name, val in sorted(env.items())]

    def delete_runs(self, **opts):
        self._guild_cmd("runs delete", _delete_runs_args(**opts))

    def restore_runs(self, **opts):
        self._guild_cmd("runs restore", _restore_runs_args(**opts))

    def purge_runs(self, **opts):
        self._guild_cmd("runs purge", _purge_runs_args(**opts))

    def label_runs(self, **opts):
        self._guild_cmd("runs label", _label_runs_args(**opts))

    def tag_runs(self, **opts):
        self._guild_cmd("runs tag", _tag_runs_args(**opts))

    def comment_runs(self, **opts):
        self._guild_cmd("runs comment", _comment_runs_args(**opts))

    def run_info(self, **opts):
        self._guild_cmd("runs info", _run_info_args(**opts))

    def check(self, **opts):
        self._print_remote_info()
        self._guild_cmd("check", _check_args(**opts))

    def _print_remote_info(self):
        sys.stdout.write(f"remote:                    {self.name} (ssh)\n")
        sys.stdout.write(f"host:                      {self.host}\n")
        sys.stdout.flush()

    def stop_runs(self, **opts):
        self._guild_cmd("runs stop", _stop_runs_args(**opts))

    def list_files(self, **opts):
        self._guild_cmd("ls", _ls_args(**opts), {"NO_HEADER_PATH": "1"})

    def diff_runs(self, **opts):
        self._guild_cmd("runs diff", _diff_args(**opts))

    def cat(self, **opts):
        self._guild_cmd("cat", _cat_args(**opts))


def _join_args(args):
    try:
        return " ".join(args)
    except TypeError:
        assert False, args


class _noquote:
    """Wraper to signify that a value must not be quoted."""

    def __init__(self, val):
        self.val = val

    def __nonzero__(self):
        return bool(self.val)

    __bool__ = __nonzero__


def _quote_arg(arg):
    """Returns arg, quoted as needed.

    Special handling for args starting and ending with double-quotes -
    these are assumed to be quoted and are returned unmodified.
    """
    if isinstance(arg, _noquote):
        return arg.val
    return util.shlex_quote(arg)


def _noquote_arg(arg):
    """Returns value denoted as one not to be quoted by _quote_arg.

    Use for paths that should not be quoted to support variable
    substitution.
    """
    if arg is None:
        return None
    return ""


def _list_runs_filter_args(
    deleted=False,
    all=False,
    more=False,
    limit=False,
    comments=False,
    verbose=False,
    **filters,
):
    args = []
    if all:
        args.append("--all")
    args.extend(_filter_and_status_args(**filters))
    if deleted:
        args.append("--deleted")
    if more > 0:
        args.append("-" + ("m" * more))
    if limit:
        args.extend(["--limit", str(limit)])
    if comments:
        args.append("--comments")
    if verbose:
        args.append("--verbose")
    return args


def _filtered_runs_filter_opts(**filters):
    opts = _filter_and_status_args(**filters)
    opts.append("--json")
    return opts


def _filter_and_status_args(
    filter_expr,
    filter_comments,
    filter_digest,
    filter_labels,
    filter_marked,
    filter_ops,
    filter_started,
    filter_tags,
    filter_unlabeled,
    filter_unmarked,
    status_completed,
    status_error,
    status_pending,
    status_running,
    status_staged,
    status_terminated,
    status_chars,
):
    filter_args = _filter_args(
        filter_expr,
        filter_comments,
        filter_digest,
        filter_labels,
        filter_marked,
        filter_ops,
        filter_started,
        filter_tags,
        filter_unlabeled,
        filter_unmarked,
    )
    status_args = _status_args(
        status_completed,
        status_error,
        status_pending,
        status_running,
        status_staged,
        status_terminated,
        status_chars,
    )
    return filter_args + status_args


def _filter_args(
    filter_expr,
    filter_comments,
    filter_digest,
    filter_labels,
    filter_marked,
    filter_ops,
    filter_started,
    filter_tags,
    filter_unlabeled,
    filter_unmarked,
):
    args = []
    if filter_expr:
        args.extend(["--filter", filter_expr])
    for val in filter_comments:
        args.extend(["--comment", val])
    if filter_digest:
        args.extend(["--digest", filter_digest])
    for val in filter_labels:
        args.extend(["--label", val])
    if filter_marked:
        args.append("--marked")
    for val in filter_ops:
        args.extend(["--operation", val])
    if filter_started:
        args.extend(["--started", filter_started])
    for val in filter_tags:
        args.extend(["--tag", val])
    if filter_unlabeled:
        args.append("--unlabled")
    if filter_unmarked:
        args.append("--unmarked")
    return args


def _status_args(
    status_completed,
    status_error,
    status_pending,
    status_running,
    status_staged,
    status_terminated,
    status_chars,  # pylint: disable=unused-argument
):
    # Ignore status_chars if provided as the status is reflected in
    # the other status attrs.
    args = []
    if status_completed:
        args.append("--completed")
    if status_error:
        args.append("--error")
    if status_pending:
        args.append("--pending")
    if status_running:
        args.append("--running")
    if status_staged:
        args.append("--staged")
    if status_terminated:
        args.append("--terminated")
    return args


def _op_src(opspec):
    opdef = op_util.opdef_for_opspec(opspec)
    src = opdef.guildfile.dir
    if src is None:
        return None
    if not os.path.isdir(src):
        raise remotelib.OperationError(
            f"cannot find source location for operation '{opspec}'"
        )
    if not os.path.exists(os.path.join(src, "guild.yml")):
        raise remotelib.OperationError(
            f"source location for operation '{opspec}' ({src}) does not "
            "contain guild.yml"
        )
    return src


def _build_package(src_dir, dist_dir):
    from guild.commands import package_impl

    log.info("Building package")
    log.info("package src: %s", src_dir)
    log.info("package dist: %s", dist_dir)
    args = click_util.Args(
        clean=True,
        dist_dir=dist_dir,
        upload=False,
        sign=False,
        identity=None,
        user=None,
        password=None,
        skip_existing=False,
        comment=None,
        capture_output=False,
    )
    with config.SetCwd(src_dir):
        package_impl.main(args)


def _run_args(
    additional_deps,
    batch_comment,
    batch_label,
    batch_tags,
    comment,
    fail_on_trial_error,
    force_deps,
    force_flags,
    force_sourcecode,
    gpus,
    label,
    keep_batch,
    keep_run,
    max_trials,
    maximize,
    minimize,
    needed,
    no_gpus,
    op_flags,
    opspec,
    opt_flags,
    optimize,
    optimizer,
    pidfile,
    proto,
    quiet,
    random_seed,
    run_dir,
    stage,
    stage_trials,
    start,
    stop_after,
    tags,
    yes,
):
    args = []
    for dep in additional_deps:
        args.extend(["--dep", dep])
    if batch_comment:
        args.extend(["--batch-comment", batch_comment])
    if batch_label:
        args.extend(["--batch-label", batch_label])
    for tag in batch_tags:
        args.extend(["--batch-tag", tag])
    if comment:
        args.extend(["--comment", comment])
    if fail_on_trial_error:
        args.append("--fail-on-trial-error")
    if force_deps:
        args.append("--force-deps")
    if force_flags:
        args.append("--force-flags")
    if force_sourcecode:
        args.append("--force-sourcecode")
    if gpus:
        args.extend(["--gpus", gpus])
    if label:
        args.extend(["--label", label])
    if keep_batch:
        args.extend("--keep-batch")
    if keep_run:
        args.extend("--keep-run")
    if max_trials is not None:
        args.extend(["--max-trials", str(max_trials)])
    if maximize:
        args.extend(["--maximize", maximize])
    if minimize:
        args.extend(["--minimize", minimize])
    if needed:
        args.append("--needed")
    if no_gpus:
        args.append("--no-gpus")
    for opt_flag_assign in opt_flags:
        args.extend(["--opt-flag", opt_flag_assign])
    if optimize:
        args.append("--optimize")
    if optimizer:
        args.extend(["--optimizer", optimizer])
    if pidfile:
        args.extend(["--pidfile", pidfile])
    if proto:
        args.extend(["--proto", proto])
    if quiet:
        args.append("--quiet")
    if random_seed is not None:
        args.extend(["--random-seed", str(random_seed)])
    if run_dir:
        args.extend(["--run-dir", run_dir])
    if stage:
        args.append("--stage")
    if stage_trials:
        args.append("--stage-trials")
    if start:
        args.extend(["--start", start])
    if stop_after:
        args.extend(["--stop-after", str(stop_after)])
    for tag in tags:
        args.extend(["--tag", tag])
    if yes:
        args.append("--yes")
    if opspec:
        args.append(opspec)
    args.extend(op_flags)
    return args


def _watch_run_args(run, pid, **filters):
    if pid:
        # Ignore other opts if pid is specified
        return ["--pid", pid]
    args = _filter_args(**filters)
    if run:
        args.append(run)
    return args


def _delete_runs_args(runs, permanent, yes, **filters):
    args = _filter_and_status_args(**filters)
    if permanent:
        args.append("-p")
    if yes:
        args.append("-y")
    args.extend(runs)
    return args


def _run_info_args(run, env, deps, all_scalars, json, comments, manifest, **filters):
    args = _filter_and_status_args(**filters)
    if env:
        args.append("--env")
    if deps:
        args.append("--deps")
    if all_scalars:
        args.append("--all-scalars")
    if json:
        args.append("--json")
    if comments:
        args.append("--comments")
    if manifest:
        args.append("--manifest")
    if run:
        args.append(run)
    return args


def _check_args(tensorflow, pytorch, verbose, offline, space, version, env):
    args = []
    if tensorflow:
        args.append("--tensorflow")
    if pytorch:
        args.append("--pytorch")
    if verbose:
        args.append("-v")
    if offline:
        args.append("--offline")
    if space:
        args.append("--space")
    if version:
        args.extend(["--version", version])
    if env:
        args.append("--env")
    return args


def _stop_runs_args(runs, no_wait, yes, **filters):
    args = _filter_args(**filters)
    if no_wait:
        args.append("-n")
    if yes:
        args.append("-y")
    args.extend(runs)
    return args


def _restore_runs_args(runs, yes, **filters):
    args = _filter_and_status_args(**filters)
    if yes:
        args.append("-y")
    args.extend(runs)
    return args


def _purge_runs_args(runs, yes, **filters):
    args = _filter_and_status_args(**filters)
    if yes:
        args.append("-y")
    args.extend(runs)
    return args


def _label_runs_args(runs, set, prepend, append, remove, clear, yes, **filters):
    args = _filter_and_status_args(**filters)
    if yes:
        args.append("-y")
    if set:
        args.extend(["-s", set])
    elif prepend:
        args.extend(["-p", prepend])
    elif append:
        args.extend(["-a", append])
    elif remove:
        args.extend(["-m", remove])
    elif clear:
        args.append("-c")
    else:
        assert False, "expected one of: set, prepend, append, remove, or clear"
    args.extend(runs)
    return args


def _tag_runs_args(runs, add, delete, clear, sync_labels, list_all, yes, **filters):
    args = _filter_and_status_args(**filters)
    if yes:
        args.append("-y")
    for tag in add:
        args.extend(["-a", tag])
    for tag in delete:
        args.extend(["-d", tag])
    if clear:
        args.append("-c")
    if sync_labels:
        args.append("-s")
    if list_all:
        args.append("--list-all")
    args.extend(runs)
    return args


def _comment_runs_args(runs, list, add, delete, clear, user, yes, **filters):
    args = _filter_and_status_args(**filters)
    if list:
        args.append("--list")
    if add:
        args.extend(["--add", add])
    if delete:
        args.extend(["--delete", str(delete)])
    if clear:
        args.append("--clear")
    if user:
        args.extend(["--user", user])
    if yes:
        args.append("-y")
    args.extend(runs)
    return args


def _ls_args(
    run, all, follow_links, human_readable, no_format, path, sourcecode, **filters
):
    args = _filter_and_status_args(**filters)
    if all:
        args.append("-a")
    if follow_links:
        args.append("-L")
    if no_format:
        args.append("-n")
    if path:
        args.extend(["-p", path])
    if sourcecode:
        args.append("--sourcecode")
    if human_readable:
        args.append("-h")
    if run:
        args.append(run)
    return args


def _diff_args(
    run,
    other_run,
    output,
    sourcecode,
    env,
    flags,
    attrs,
    deps,
    paths,
    cmd,
    working,
    dir,
    **filters,
):
    args = _filter_and_status_args(**filters)
    if output:
        args.append("--output")
    if sourcecode:
        args.append("--sourcecode")
    if flags:
        args.append("--flags")
    if env:
        args.append("--env")
    if attrs:
        args.append("--attrs")
    if deps:
        args.append("--deps")
    for path in paths:
        args.extend(["--path", path])
    args.extend(["--cmd", cmd or DEFAULT_DIFF_CMD])
    if working:
        args.append("--working")
    if dir:
        args.extend(["--dir", dir])
    if run:
        args.append(run)
    if other_run:
        args.append(other_run)
    return args


def _cat_args(run, path, sourcecode, output, **filters):
    args = _filter_and_status_args(**filters)
    if run:
        args.append(run)
    if path:
        args.extend(["-p", path])
    if sourcecode:
        args.append("--sourcecode")
    if output:
        args.append("--output")
    return args
