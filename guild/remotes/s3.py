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

import itertools
import logging
import os
import subprocess
import sys
import uuid

from guild import remote as remotelib
from guild import remote_util
from guild import util
from guild import var

from . import meta_sync

log = logging.getLogger("guild.remotes.s3")

RUNS_PATH = ["runs"]
DELETED_RUNS_PATH = ["trash", "runs"]


class S3RemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return S3Remote(name, config)

    def remote_for_spec(self, spec):
        bucket, root = _parse_spec(spec)
        assert root.startswith("/")
        name = _remote_name(bucket, root)
        config = remotelib.RemoteConfig(
            {
                "bucket": bucket,
                "root": root,
            }
        )
        return S3Remote(name, config)


def _parse_spec(spec):
    parts = spec.split("/", 1)
    if len(parts) == 1:
        return parts[0], "/"
    else:
        assert len(parts) == 2, parts
        return parts[0], "/" + parts[1]


def _remote_name(bucket, root):
    if root != "/":
        return "s3:%s%s" % (bucket, root)
    return "s3:%s" % bucket


class S3Remote(meta_sync.MetaSyncRemote):
    def __init__(self, name, config):
        self.name = name
        self.bucket = config["bucket"]
        self.root = config.get("root", "/")
        self.region = config.get("region")
        self.local_env = remote_util.init_env(config.get("local-env"))
        self.local_sync_dir = meta_sync.local_meta_dir(name, self._s3_uri())
        runs_dir = os.path.join(self.local_sync_dir, *RUNS_PATH)
        deleted_runs_dir = os.path.join(self.local_sync_dir, *DELETED_RUNS_PATH)
        super(S3Remote, self).__init__(runs_dir, deleted_runs_dir)

    def _s3_uri(self, *subpath):
        joined_path = _join_path(self.root, *subpath)
        return "s3://%s/%s" % (self.bucket, joined_path)

    def _sync_runs_meta(self, force=False):
        remote_util.remote_activity("Refreshing run info for %s" % self.name)
        if not force and self._meta_current():
            return
        meta_sync.clear_local_meta_id(self.local_sync_dir)
        sync_args = [
            self._s3_uri(),
            self.local_sync_dir,
            "--exclude",
            "*",
            "--include",
            "*/.guild/opref",
            "--include",
            "*/.guild/attrs/*",
            "--include",
            "*/.guild/LOCK*",
            "--include",
            "meta-id",
            "--delete",
        ]
        self._s3_cmd("sync", sync_args, quiet=True)

    def _meta_current(self):
        return meta_sync.meta_current(self.local_sync_dir, self._remote_meta_id)

    def _remote_meta_id(self):
        with util.TempFile("guild-s3-") as tmp:
            args = [
                "--bucket",
                self.bucket,
                "--key",
                _join_path(self.root, "meta-id"),
                tmp.path,
            ]
            self._s3api_output("get-object", args)
            return open(tmp.path, "r").read().strip()

    def _s3api_output(self, name, args):
        cmd = [_aws_cmd()]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3api", name] + args)
        log.debug("aws cmd: %r", cmd)
        try:
            return subprocess.check_output(
                cmd, env=self._cmd_env(), stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.for_called_process_error(e)

    def _cmd_env(self):
        env = dict(os.environ)
        if self.local_env:
            env.update(self.local_env)
        return env

    def _s3_cmd(self, name, args, quiet=False):
        cmd = [_aws_cmd()]
        if self.region:
            cmd.extend(["--region", self.region])
        cmd.extend(["s3", name] + args)
        log.debug("aws cmd: %r", cmd)
        try:
            remote_util.subprocess_call(cmd, extra_env=self.local_env, quiet=quiet)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.for_called_process_error(e)

    def _delete_runs(self, runs, permanent):
        for run in runs:
            run_uri = self._s3_uri(*(RUNS_PATH + [run.id]))
            if permanent:
                self._s3_rm(run_uri)
            else:
                deleted_uri = self._s3_uri(*(DELETED_RUNS_PATH + [run.id]))
                self._s3_mv(run_uri, deleted_uri)
        self._new_meta_id()

    def _s3_rm(self, uri):
        rm_args = ["--recursive", uri]
        self._s3_cmd("rm", rm_args)

    def _s3_mv(self, src, dest):
        mv_args = ["--recursive", src, dest]
        self._s3_cmd("mv", mv_args)

    def _restore_runs(self, runs):
        for run in runs:
            deleted_uri = self._s3_uri(*(DELETED_RUNS_PATH + [run.id]))
            restored_uri = self._s3_uri(*(RUNS_PATH + [run.id]))
            self._s3_mv(deleted_uri, restored_uri)
        self._new_meta_id()

    def _purge_runs(self, runs):
        for run in runs:
            uri = self._s3_uri(*(DELETED_RUNS_PATH + [run.id]))
            self._s3_rm(uri)
        self._new_meta_id()

    def status(self, verbose=False):
        try:
            self._s3api_output("get-bucket-location", ["--bucket", self.bucket])
        except remotelib.RemoteProcessError as e:
            self._handle_status_error(e)
        else:
            sys.stdout.write(
                "%s (S3 bucket %s) is available\n" % (self.name, self.bucket)
            )

    def _handle_status_error(self, e):
        output = e.output.decode()
        if "NoSuchBucket" in output:
            raise remotelib.OperationError(
                "%s is not available - %s does not exist" % (self.name, self.bucket)
            )
        else:
            raise remotelib.OperationError(
                "%s is not available: %s" % (self.name, output)
            )

    def start(self):
        log.info("Creating S3 bucket %s", self.bucket)
        try:
            self._s3_cmd("mb", ["s3://%s" % self.bucket])
        except remotelib.RemoteProcessError:
            raise remotelib.OperationError()

    def reinit(self):
        self.start()

    def stop(self):
        log.info("Deleting S3 bucket %s", self.bucket)
        try:
            self._s3_cmd("rb", ["--force", "s3://%s" % self.bucket])
        except remotelib.RemoteProcessError:
            raise remotelib.OperationError()

    def stop_details(self):
        return "S3 bucket %s will be deleted - THIS CANNOT BE UNDONE!" % self.bucket

    def push(self, runs, delete=False):
        for run in runs:
            self._push_run(run, delete)
            self._new_meta_id()
        self._sync_runs_meta(force=True)

    def _push_run(self, run, delete):
        local_run_src = os.path.join(run.path, "")
        remote_run_dest = self._s3_uri(*RUNS_PATH + [run.id]) + "/"
        args = ["--no-follow-symlinks", local_run_src, remote_run_dest]
        if delete:
            args.insert(0, "--delete")
        log.info("Copying %s to %s", run.id, self.name)
        self._s3_cmd("sync", args, quiet=True)

    def _new_meta_id(self):
        meta_id = uuid.uuid4().hex
        with util.TempFile("guild-s3-") as tmp:
            with open(tmp.path, "w") as f:
                f.write(meta_id)
            args = [
                "--bucket",
                self.bucket,
                "--key",
                _join_path(self.root, "meta-id"),
                "--body",
                tmp.path,
            ]
            self._s3api_output("put-object", args)

    def pull(self, runs, delete=False):
        for run in runs:
            self._pull_run(run, delete)

    def _pull_run(self, run, delete):
        remote_run_src = self._s3_uri(*RUNS_PATH + [run.id]) + "/"
        local_run_dest = os.path.join(var.runs_dir(), run.id, "")
        args = [remote_run_src, local_run_dest]
        if delete:
            args.insert(0, "--delete")
        log.info("Copying %s from %s", run.id, self.name)
        self._s3_cmd("sync", args)


def _aws_cmd():
    cmd = util.which("aws")
    if not cmd:
        raise remotelib.OperationError(
            "AWS Command Line Interface (CLI) is not available\n"
            "Refer to https://docs.aws.amazon.com/cli for help installing it."
        )
    return cmd


def _join_path(root, *parts):
    path = [part for part in itertools.chain([root], parts) if part not in ("/", "")]
    return "/".join(path)
