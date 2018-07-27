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

    def push(self, runs, verbose=False):
        for run in runs:
            self._push_run(run, verbose)

    def push_dest(self):
        return "{}:{}".format(self.host, self.guild_home)

    def _push_run(self, run, verbose):
        opts = "-al"
        if verbose:
            opts += "v"
        src = run.path + "/"
        dest = "{}:{}/runs/{}/".format(self.host, self.guild_home, run.id)
        cmd = ["rsync", opts, src, dest]
        log.info("Copying %s", run.id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def pull(self, run_ids, verbose=False):
        for run_id in run_ids:
            self._pull_run(run_id, verbose)

    def _pull_run(self, run_id, verbose):
        src = "{}:{}/runs/{}/".format(self.host, self.guild_home, run_id)
        dest = os.path.join(var.runs_dir(), run_id + "/")
        cmd = ["rsync"] + self._rsync_opts(verbose) + [src, dest]
        log.info("Copying %s", run_id)
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def pull_all(self, verbose=False):
        src = "{}:{}/runs/".format(self.host, self.guild_home)
        dest = var.runs_dir() + "/"
        cmd = ["rsync"] + self._rsync_opts(verbose) + [src, dest]
        log.info("Copying all runs")
        log.debug("rsync cmd: %r", cmd)
        subprocess.check_call(cmd)

    def pull_src(self):
        return "{}:{}".format(self.host, self.guild_home)

    @staticmethod
    def _rsync_opts(verbose):
        opts = ["-al", "--inplace"]
        if verbose:
            opts.append("-v")
        return opts

    def start(self):
        raise guild.remote.OperationNotSupported(
            "start is not supported for ssh remotes")

    def stop(self):
        raise guild.remote.OperationNotSupported(
            "stop is not supported for ssh remotes")

    def status(self, verbose=False):
        ssh_util.ssh_ping(self.host, verbose)
        sys.stdout.write("%s (%s) is available\n" % (self.name, self.host))
