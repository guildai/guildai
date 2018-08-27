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
import itertools
import logging
import os
import subprocess
import sys

from guild import cli
from guild import click_util
from guild import remote as remotelib
from guild import remote_util
from guild import var

from guild.commands import runs_impl

log = logging.getLogger("guild.remotes.s3")

RUNS_PATH = ["runs"]
DELETED_RUNS_PATH = ["trash", "runs"]

class S3Remote(remotelib.Remote):

    def __init__(self, name, config):
        self.name = name
        self.bucket = config["bucket"]
        self.root = config.get("root", "/")
        self.region = config.get("region")
        self.local_sync_dir = lsd = self._local_sync_dir()
        self._runs_dir = os.path.join(lsd, *RUNS_PATH)
        self._deleted_runs_dir = os.path.join(lsd, *DELETED_RUNS_PATH)

    def _local_sync_dir(self):
        base_dir = var.remote_dir(self.name)
        uri_hash = hashlib.md5(self._s3_uri().encode()).hexdigest()
        return os.path.join(base_dir, "meta", uri_hash)

    def _s3_uri(self, *subpath):
        path = [
            part for part in itertools.chain([self.root], subpath)
            if part not in ("/", "")]
        joined_path = "/".join(path)
        return "s3://%s/%s" % (self.bucket, joined_path)

    def list_runs(self, verbose, **filters):
        self._verify_creds_and_region()
        self._sync_runs_meta()
        runs_dir = self._runs_dir_for_filters(**filters)
        if not os.path.exists(runs_dir):
            return
        args = click_util.Args(verbose=verbose, **filters)
        args.archive = runs_dir
        args.deleted = False
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
        sync_args = [
            self._s3_uri(),
            self.local_sync_dir,
            "--exclude", "*",
            "--include", "*/.guild/*",
            "--delete",
        ]
        log.info("Synchronizing runs with %s", self.name)
        self._s3_cmd("sync", sync_args, to_stderr=True)

    def _s3api_output(self, name, args):
        cmd = ["aws"]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3api", name] + args)
        log.debug("aws cmd: %r", cmd)
        try:
            return subprocess.check_output(
                cmd,
                env=os.environ,
                stderr=subprocess.STDOUT)
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

    def delete_runs(self, **opts):
        self._verify_creds_and_region()
        self._sync_runs_meta()
        args = click_util.Args(**opts)
        args.archive = self._runs_dir
        if args.permanent:
            preview = (
                "WARNING: You are about to permanently delete "
                "the following runs from %s:" % self.name)
            confirm = "Permanently delete these runs?"
        else:
            preview = (
                "You are about to delete the following runs from %s:"
                % self.name)
            confirm = "Delete these runs?"
        no_runs_help = "Nothing to delete."
        def delete_f(selected):
            self._delete_runs(selected, args.permanent)
            self._sync_runs_meta()
        try:
            runs_impl._runs_op(
                args, None, False, preview, confirm, no_runs_help,
                delete_f, confirm_default=not args.permanent)
        except SystemExit as e:
            self._reraise_system_exit(e)

    def _reraise_system_exit(self, e):
        if not e.args[0]:
            raise e
        exit_code = e.args[1]
        msg = e.args[0].replace(
            "guild runs list",
            "guild runs list -r %s" % self.name)
        raise SystemExit(msg, exit_code)

    def _delete_runs(self, runs, permanent):
        for run in runs:
            run_uri = self._s3_uri(*(RUNS_PATH + [run.id]))
            if permanent:
                self._s3_rm(run_uri)
            else:
                deleted_uri = self._s3_uri(*(DELETED_RUNS_PATH + [run.id]))
                self._s3_mv(run_uri, deleted_uri)

    def _s3_rm(self, uri):
        rm_args = ["--recursive", uri]
        self._s3_cmd("rm", rm_args)

    def _s3_mv(self, src, dest):
        mv_args = ["--recursive", src, dest]
        self._s3_cmd("mv", mv_args)

    def status(self, verbose=False):
        self._verify_creds_and_region()
        try:
            self._s3api_output(
                "get-bucket-location",
                ["--bucket", self.bucket])
        except remotelib.RemoteProcessError as e:
            self._handle_status_error(e)
        else:
            sys.stdout.write(
                "%s (S3 bucket %s) is available\n"
                % (self.name, self.bucket))

    def _handle_status_error(self, e):
        output = e.output.decode()
        if "NoSuchBucket" in output:
            cli.error(
                "%s is not available (%s does not exist)"
                % (self.name, self.bucket))
        else:
            cli.error(
                "%s is not available: %s"
                % (self.name, output))

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
