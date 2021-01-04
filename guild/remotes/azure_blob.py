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

log = logging.getLogger("guild.remotes.azure_blob")

RUNS_PATH = ["runs"]
DELETED_RUNS_PATH = ["trash", "runs"]


class AzureBlobStorageRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return AzureBlobStorageRemote(name, config)

    def remote_for_spec(self, spec):
        raise NotImplementedError()


class AzureBlobStorageRemote(meta_sync.MetaSyncRemote):
    def __init__(self, name, config):
        self.name = name
        self.container = config["container"]
        self.root = config.get("root", "/")
        self.local_env = remote_util.init_env(config.get("local-env"))
        self.local_sync_dir = meta_sync.local_meta_dir(name, self._container_path())
        runs_dir = os.path.join(self.local_sync_dir, *RUNS_PATH)
        super(AzureBlobStorageRemote, self).__init__(runs_dir, None)

    def _container_path(self, *path_parts):
        all_parts = path_parts if not self.root else (self.root,) + path_parts
        if not all_parts:
            return self.container
        return self.container + "/" + "/".join(all_parts)

    def _sync_runs_meta(self, force=False):
        remote_util.remote_activity("Refreshing run info for %s" % self.name)
        if not force and meta_sync.meta_current(
            self.local_sync_dir, self._remote_meta_id
        ):
            return
        _ensure_azure_local_dir(self.local_sync_dir)
        meta_sync.clear_local_meta_id(self.local_sync_dir)
        # TODO: This is a terribly ineffecient approach as we're
        # copying everything just to get metadata for the runs. The
        # azcopy sync command has limited include/exclude pattern
        # support which makes it hard to use for this
        # application. Copying metadata for each remote run would
        # likely be quite inefficient as well, though certainly less
        # impacting on local storage.
        sync_args = [
            self._container_path(),
            self.local_sync_dir,
            "--delete-destination",
            "true",
        ]
        self._azcopy("sync", sync_args, quiet=True)

    def _remote_meta_id(self):
        with util.TempFile("guild-azure-blob-") as tmp:
            args = [self._container_path("meta-id"), tmp.path]
            self._azcopy("copy", args, quiet=True)
            return open(tmp.path, "r").read().strip()

    def _azcopy(self, cmd_name, args, quiet=False):
        cmd = [_azcopy_cmd(), cmd_name] + args
        log.debug("azcopy: %r", cmd)
        try:
            remote_util.subprocess_call(cmd, extra_env=self.local_env, quiet=quiet)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.for_called_process_error(e)

    def _delete_runs(self, runs, permanent):
        for run in runs:
            run_path = self._container_path(*(RUNS_PATH + [run.id]))
            if permanent:
                self._azcopy("remove", [run_path, "--recursive"])
            else:
                deleted_path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
                # TODO: We want a simple move/rename here but it looks
                # like azcopy requires copy+delete. The copy from a
                # blob for some reason requires a SAS token. Stubbing
                # this out for now.
                self._azcopy("copy", [run_path, deleted_path, "--recursive"])
                self._azcopy("remove", [run_path, "--recursive"])
        self._new_meta_id()

    def _restore_runs(self, runs):
        for run in runs:
            deleted_path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
            restored_path = self._container_path(*(RUNS_PATH + [run.id]))
            # TODO: See _delete_runs above. Same problem applies here.
            self._azcopy("copy", [deleted_path, restored_path, "--recursive"])
            self._azcopy("remove", [deleted_path, "--recursive"])
        self._new_meta_id()

    def _purge_runs(self, runs):
        for run in runs:
            path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
            self._azsync("remove", [path, "--recursive"])
        self._new_meta_id()

    def status(self, verbose=False):
        path = self._container_path()
        try:
            self._azcopy("ls", [path], quiet=True)
        except remotelib.RemoteProcessError as e:
            self._handle_status_error(e)
        else:
            sys.stdout.write("%s (%s) is available\n" % (self.name, path))

    def _handle_status_error(self, e):
        output = e.output.decode()
        if "NoSuchBucket" in output:
            raise remotelib.OperationError(
                "%s is not available - %s does not exist" % (self.name, self.container)
            )
        else:
            raise remotelib.OperationError(
                "%s is not available: %s" % (self.name, output)
            )

    def push(self, runs, delete=False):
        for run in runs:
            self._push_run(run, delete)
            self._new_meta_id()
        self._sync_runs_meta(force=True)

    def _push_run(self, run, delete):
        local_run_src = os.path.join(run.path, "")
        remote_run_dest = self._container_path(*RUNS_PATH + [run.id])
        args = [local_run_src, remote_run_dest]
        if delete:
            args[:0] = ["--delete-destination", "true"]
        log.info("Copying %s to %s", run.id, self.name)
        self._azcopy("sync", args)

    def _new_meta_id(self):
        meta_id = uuid.uuid4().hex
        with util.TempFile("guild-azure-blob-") as tmp:
            with open(tmp.path, "w") as f:
                f.write(meta_id)
            args = [tmp.path, self._container_path("meta-id")]
            self._azcopy("copy", args)

    def pull(self, runs, delete=False):
        for run in runs:
            self._pull_run(run, delete)

    def _pull_run(self, run, delete):
        remote_run_src = self._container_path(*RUNS_PATH + [run.id])
        local_run_dest = os.path.join(var.runs_dir(), run.id)
        args = [remote_run_src, local_run_dest]
        if delete:
            args[:0] = ["--delete-destination", "true"]
        log.info("Copying %s from %s", run.id, self.name)
        util.ensure_dir(local_run_dest)
        self._azcopy("sync", args)


def _azcopy_cmd():
    cmd = util.which("azcopy")
    if not cmd:
        raise remotelib.OperationError(
            "AzCopy is not available\n"
            "Refer to https://docs.microsoft.com/en-us/azure/storage/"
            "common/storage-use-azcopy-v10 for help installing it."
        )
    return cmd


def _ensure_azure_local_dir(dir):
    """Creates dir if it doesn't exist.

    azcopy doesn't know it's a local directory if it doesn't exist.
    """
    util.ensure_dir(dir)
