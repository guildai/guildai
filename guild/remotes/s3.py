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
import sys

from guild import click_util
from guild import remote as remotelib
from guild import remote_util
from guild import var

from guild.commands import runs_impl

log = logging.getLogger("guild.remotes.s3")

class S3Remote(remotelib.Remote):

    def __init__(self, name, config):
        self.name = name
        self.bucket = bucket = config["bucket"]
        self.root = root = config.get("root", "/")
        self.region = config.get("region")
        self.local_sync_dir = lsd = self._local_sync_dir(name, bucket, root)
        self._runs_dir = os.path.join(lsd, "runs")
        self._deleted_runs_dir = os.path.join(lsd, "trash", "runs")

    @staticmethod
    def _local_sync_dir(name, bucket, root):
        base_dir = var.remote_dir(name)
        full_src = _s3_path_join(bucket, root)
        uri_hash = hashlib.md5(full_src.encode()).hexdigest()
        return os.path.join(base_dir, "meta", uri_hash)

    def list_runs(self, verbose, **filters):
        self._verify_creds_and_region()
        self._sync_runs_meta()
        runs_dir = self._runs_dir_for_filters(**filters)
        if not os.path.exists(runs_dir):
            return
        args = click_util.Args(verbose=verbose, **filters)
        args.archive = runs_dir
        args.remote = False
        runs_impl.list_runs(args)

    def _runs_dir_for_filters(self, deleted, **_filters):
        if deleted:
            return self._deleted_runs_dir
        else:
            return self._runs_dir

    def _verify_creds_and_region(self):
        remote_util.require_env("AWS_ACCESS_KEY_ID")
        remote_util.require_env("AWS_SECRET_ACCESS_KEY")
        if not self.region:
            remote_util.require_env("AWS_DEFAULT_REGION")

    def _sync_runs_meta(self):
        s3_path = _s3_path_join(self.bucket, self.root)
        args = [
            "s3://%s" % s3_path,
            self.local_sync_dir,
            "--exclude", "*",
            "--include", "*/.guild/*",
            "--delete",
        ]
        log.info("Synchrozing runs with %s", s3_path)
        self._s3_cmd("sync", args, to_stderr=True)

    def _s3api_cmd(self, name, args):
        cmd = ["aws"]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3api", name] + args)
        log.debug("aws cmd: %r", cmd)
        try:
            return subprocess.check_output(cmd, env=os.environ)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.from_called_process_error(e)

    def _s3_cmd(self, name, args, to_stderr=False):
        cmd = ["aws"]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3", name] + args)
        log.debug("aws cmd: %r", cmd)
        try:
            if to_stderr:
                _subprocess_call_to_stderr(cmd)
            else:
                subprocess.check_call(cmd, env=os.environ)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.from_called_process_error(e)

def _subprocess_call_to_stderr(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ)
    while True:
        line = p.stdout.readline()
        if not line:
            break
        sys.stderr.write(line.decode())

def _s3_path_join(*parts):
    parts = [part for part in parts if part not in ("/", "")]
    return "/".join(parts)

def _list(d):
    try:
        return os.listdir(d)
    except OSError as e:
        if e.errno != 2:
            raise
        return []

def _ids_from_prefixes(prefixes):
    def strip(s):
        if s.endswith("/"):
            return s[:-1]
        return s
    return [strip(p) for p in prefixes]
