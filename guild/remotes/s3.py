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

import hashlib
import logging
import os
import subprocess

from guild import click_util
from guild import remote as remotelib
from guild import remote_util
from guild import util
from guild import var

from guild.commands import runs_impl

log = logging.getLogger("guild.remotes.s3")

class S3Remote(remotelib.Remote):

    def __init__(self, name, config):
        self.name = name
        self.uri = uri = util.strip_trailing_path(config["uri"])
        self.region = config.get("region")
        self.meta_dir = self._meta_dir(name, uri)

    @staticmethod
    def _meta_dir(name, uri):
        base_dir = var.remote_dir(name)
        uri_hash = hashlib.md5(uri.encode()).hexdigest()
        return os.path.join(base_dir, "meta", uri_hash)

    def list_runs(self, verbose, **filters):
        self._verify_creds_and_region()
        runs_dir = self._sync_runs_meta(filters.get("deleted", False))
        if not os.path.exists(runs_dir):
            return
        args = click_util.Args(verbose=verbose, **filters)
        args.archive = runs_dir
        args.remote = False
        runs_impl.list_runs(args)

    def _verify_creds_and_region(self):
        remote_util.require_env("AWS_ACCESS_KEY_ID")
        remote_util.require_env("AWS_SECRET_ACCESS_KEY")
        if not self.region:
            remote_util.require_env("AWS_DEFAULT_REGION")

    def _sync_runs_meta(self, deleted):
        util.ensure_dir(self.meta_dir)
        if deleted:
            sync_src = self.uri + "/trash/runs/"
            sync_target = os.path.join(self.meta_dir, "trash", "runs")
        else:
            sync_src = self.uri + "/runs/"
            sync_target = os.path.join(self.meta_dir, "runs")
        for run_id in self._ls_pre(sync_src):
            print("TODO: get .guild/attrs and what not for {}".format(run_id))
        return sync_target

    def _ls_pre(self, src):
        out = self._s3_cmd("ls", [src])
        print("#################")
        print(out)
        return []

    def _s3_cmd(self, name, args):
        cmd = ["aws"]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3", name] + args)
        log.debug("aws cmd: %r" % cmd)
        try:
            return subprocess.check_output(cmd, env=os.environ)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.from_called_process_error(e)
