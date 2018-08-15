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

import guild.remote

from guild import var

from . import ssh_util

log = logging.getLogger("guild.remotes.ssh")

class SSHRemote(guild.remote.Remote):

    def __init__(self, name, config):
        self.name = name
        self.host = config["host"]
        self.user = config.get("user")
        self.guild_home = config.get("guild-home", ".guild")
        self.guild_env = config.get("guild-env")

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

    def run_op(self, op):
        print("TODO: run %s on %s, somehow" % (op, self.host))

    def list_runs(self, verbose=False, **filters):
        cmd_parts = []
        if self.guild_env:
            cmd_parts.append(
                "cd '%s' && QUIET=1 source guild-env"
                % self.guild_env)
            cmd_parts.append("&&")
        cmd_parts.extend(["guild", "runs", "list"])
        cmd_parts.extend(_list_runs_filter_opts(**filters))
        if verbose:
            cmd_parts.append("--verbose")
        cmd = [" ".join(cmd_parts)]
        ssh_util.ssh_cmd(self.host, cmd)

def _list_runs_filter_opts(ops, labels, unlabeled, running,
                           completed, error, terminated, deleted,
                           all, more):
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
        opts.extend(["--label", label])
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
