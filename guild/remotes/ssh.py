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
import logging
import subprocess
import sys

import six

import guild.remote

from guild import click_util
from guild import run as runlib
from guild import util
from guild import var
from guild.commands import package_impl

from . import ssh_util

log = logging.getLogger("guild.remotes.ssh")

class SSHRemote(guild.remote.Remote):

    def __init__(self, name, config):
        self.name = name
        self.host = config["host"]
        self.user = config.get("user")
        self.guild_home = config.get("guild-home", ".guild")
        self.guild_env = config.get("guild-env")
        self.run_init = config.get("run-init")

    def push(self, runs, verbose=False):
        for run in runs:
            self._push_run(run, verbose)

    def push_dest(self):
        return "{}:{}".format(self.host, self.guild_home)

    def _push_run(self, run, verbose):
        cmd = ["rsync", "-al", "--delete"]
        if verbose:
            cmd.append("-vvv")
        else:
            cmd.append("-v")
        src = run.path + "/"
        dest = "{}:{}/runs/{}/".format(self.host, self.guild_home, run.id)
        cmd.extend([src, dest])
        log.info("Copying %s", run.id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def pull(self, run_ids, verbose=False):
        for run_id in run_ids:
            self._pull_run(run_id, verbose)

    def _pull_run(self, run_id, verbose):
        src = "{}:{}/runs/{}/".format(self.host, self.guild_home, run_id)
        dest = os.path.join(var.runs_dir(), run_id + "/")
        cmd = ["rsync"] + self._pull_rsync_opts(verbose) + [src, dest]
        log.info("Copying %s", run_id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    @staticmethod
    def _pull_rsync_opts(verbose):
        opts = ["-al", "--inplace", "--delete"]
        if verbose:
            opts.append("-vvv")
        else:
            opts.append("-v")
        return opts

    def pull_all(self, verbose=False):
        src = "{}:{}/runs/".format(self.host, self.guild_home)
        dest = var.runs_dir() + "/"
        cmd = ["rsync"] + self._pull_rsync_opts(verbose) + [src, dest]
        log.info("Copying all runs")
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def pull_src(self):
        return "{}:{}".format(self.host, self.guild_home)

    def start(self):
        raise guild.remote.OperationNotSupported(
            "start is not supported for ssh remotes")

    def reinit(self):
        raise guild.remote.OperationNotSupported(
            "reinit is not supported for ssh remotes")

    def stop(self):
        raise guild.remote.OperationNotSupported(
            "stop is not supported for ssh remotes")

    def status(self, verbose=False):
        ssh_util.ssh_ping(self.host, verbose)
        sys.stdout.write("%s (%s) is available\n" % (self.name, self.host))

    def run_op(self, opspec, args, **opts):
        print("- build package dist")
        with util.TempDir(prefix="guild-remote-pkg-") as dist_dir:
            _build_package(dist_dir)
            remote_run_dir = self._init_remote_run(dist_dir, opspec)
        self._run_op(remote_run_dir, opspec, args, **opts)
        self._watch_op(remote_run_dir)

    def _init_remote_run(self, package_dist_dir, opspec):
        remote_run_dir = self._init_remote_run_dir(opspec)
        self._copy_package_dist(package_dist_dir, remote_run_dir)
        self._install_job_package(remote_run_dir)
        return remote_run_dir

    def _init_remote_run_dir(self, opspec):
        run_id = runlib.mkid()
        run_dir = os.path.join(self.guild_home, "runs", run_id)
        cmd = (
            "set -e; "
            "mkdir -p {run_dir}/.guild; "
            "touch {run_dir}/.guild/PENDING; "
            "mkdir {run_dir}/.guild/attrs; "
            "echo 'pending:? ? ? {opspec}' > {run_dir}/.guild/attrs/opref; "
            "echo \"$(date +%s)000000\" > {run_dir}/.guild/attrs/started; "
            "mkdir {run_dir}/.guild/job-packages"
            .format(run_dir=run_dir, opspec=opspec)
        )
        log.info("Initializing remote run")
        ssh_util.ssh_cmd(self.host, [cmd], self.user)
        return run_dir

    def _copy_package_dist(self, package_dist_dir, remote_run_dir):
        src = package_dist_dir + "/"
        dest = "{}:{}/.guild/job-packages/".format(self.host, remote_run_dir)
        cmd = ["rsync", "-vr", src, dest]
        log.info("Copying package")
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def _install_job_package(self, remote_run_dir):
        cmd = (
            "cd {run_dir}/.guild/job-packages;"
            "guild install *.whl --target ."
            .format(run_dir=remote_run_dir)
        )
        log.info("Installing package and its dependencies")
        ssh_util.ssh_cmd(self.host, [cmd], self.user)

    def _run_op(self, remote_run_dir, opspec, args, **opts):
        cmd_lines = ["set -e"]
        cmd_lines.extend(self._env_activate_cmd_lines())
        cmd_lines.append(
            "export PYTHONPATH={run_dir}/.guild/job-packages:$PYTHONPATH"
            .format(run_dir=remote_run_dir))
        cmd_lines.append(_remote_run_cmd(remote_run_dir, opspec, args, **opts))
        cmd = "; ".join(cmd_lines)
        log.info("Starting remote operation")
        ssh_util.ssh_cmd(self.host, [cmd], self.user)

    def _watch_op(self, remote_run_dir):
        cmd_lines = ["set -e"]
        cmd_lines.extend(self._env_activate_cmd_lines())
        cmd_lines.append(
            "NO_WATCHING_MSG=1 guild watch --pid {run_dir}/.guild/JOB"
            .format(run_dir=remote_run_dir))
        cmd = "; ".join(cmd_lines)
        log.debug("watching remote run")
        ssh_util.ssh_cmd(self.host, [cmd], self.user)

    def list_runs(self, verbose=False, **filters):
        cmd_lines = ["set -e"]
        cmd_lines.extend(self._env_activate_cmd_lines())
        opts = _list_runs_filter_opts(**filters)
        if verbose:
            opts.append("--verbose")
        cmd_lines.append("guild runs list %s" % " ".join(opts))
        cmd = "; ".join(cmd_lines)
        ssh_util.ssh_cmd(self.host, [cmd], self.user)

    def _env_activate_cmd_lines(self):
        if not self.guild_env:
            return []
        return [
            "cd %s" % self.guild_env,
            "QUIET=1 source guild-env"
        ]

def _list_runs_filter_opts(ops, labels, unlabeled, running,
                           completed, error, terminated, deleted,
                           all, more, **kw):
    assert not kw, kw
    opts = []
    if all:
        opts.append("--all")
    if completed:
        opts.append("--completed")
    if deleted:
        opts.append("--deleted")
    if error:
        opts.append("--error")
    for label in labels:
        opts.extend(["--label", six.moves.shlex_quote(label)])
    if more > 0:
        opts.append("-" + ("m" * more))
    for op in ops:
        opts.extend(["-o", op])
    if running:
        opts.append("--running")
    if terminated:
        opts.append("--terminated")
    if unlabeled:
        opts.append("--unlabeled")
    return opts

def _build_package(dist_dir):
    log.info("Building package")
    args = click_util.Args(
        dist_dir=dist_dir,
        upload=False,
        sign=False,
        identity=None,
        user=None,
        password=None,
        skip_existing=False,
        comment=None)
    package_impl.main(args)

def _remote_run_cmd(remote_run_dir, opspec, op_args, label,
                    restart, rerun, disable_plugins, gpus,
                    no_gpus, **kw):
    assert not kw, kw
    q = six.moves.shlex_quote
    cmd = [
        "NO_WARN_RUNDIR=1",
        "guild", "run", q(opspec),
        "--run-dir", remote_run_dir,
        "--background", "%s/.guild/JOB" % remote_run_dir,
        "--quiet",
        "--yes",
    ]
    if label:
        cmd.extend(["--label", q(label)])
    if restart:
        cmd.extend(["--restart", q(restart)])
    if rerun:
        cmd.extend(["--rerun", q(rerun)])
    if disable_plugins:
        cmd.extend(["--disable_plugins", q(disable_plugins)])
    if gpus:
        cmd.extend(["--gpus", q(gpus)])
    if no_gpus:
        cmd.append("--no-gpus")
    cmd.extend([q(arg) for arg in op_args])
    return " ".join(cmd)
