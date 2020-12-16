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

from guild import click_util
from guild import log as loglib
from guild import remote as remotelib
from guild import remote_util
from guild import util
from guild import var

from guild.commands import runs_impl

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


class AzureBlobStorageRemote(remotelib.Remote):
    def __init__(self, name, config):
        self.name = name
        self.container = config["container"]
        self.root = config.get("root", "/")
        self.env = _init_env(config.get("env"))
        self.local_sync_dir = lsd = self._local_sync_dir()
        self._runs_dir = os.path.join(lsd, *RUNS_PATH)
        self._deleted_runs_dir = os.path.join(lsd, *DELETED_RUNS_PATH)

    def _local_sync_dir(self):
        return remote_util.local_meta_dir(self.name, self._container_path())

    def list_runs(self, verbose=False, **filters):
        self._sync_runs_meta()
        runs_dir = self._runs_dir_for_filters(**filters)
        if not os.path.exists(runs_dir):
            return
        args = click_util.Args(verbose=verbose, **filters)
        args.archive = runs_dir
        args.deleted = False
        args.remote = None
        args.json = False
        runs_impl.list_runs(args)

    def _runs_dir_for_filters(self, deleted, **_filters):
        if deleted:
            return self._deleted_runs_dir
        else:
            return self._runs_dir

    def _sync_runs_meta(self, force=False):
        log.info(loglib.dim("Synchronizing runs with %s"), self.name)
        if not force and self._meta_current():
            return
        self._ensure_local_sync_dir()
        self._clear_local_meta_id()
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

    def _meta_current(self):
        local_id = self._local_meta_id()
        if local_id is None:
            log.debug("local meta-id not found, meta not current")
            return False
        remote_id = self._remote_meta_id()
        log.debug("local meta-id: %s", local_id)
        log.debug("remote meta-id: %s", remote_id)
        return local_id == remote_id

    def _ensure_local_sync_dir(self):
        util.ensure_dir(self.local_sync_dir)

    def _clear_local_meta_id(self):
        id_path = os.path.join(self.local_sync_dir, "meta-id")
        util.ensure_deleted(id_path)

    def _local_meta_id(self):
        id_path = os.path.join(self.local_sync_dir, "meta-id")
        return util.try_read(id_path, apply=str.strip)

    def _remote_meta_id(self):
        with util.TempFile("guild-azure-blob-") as tmp:
            args = [self._container_path("meta-id"), tmp.path]
            self._azcopy("copy", args, quiet=True)
            return open(tmp.path, "r").read().strip()

    def _s3api_output(self, name, args):
        assert False
        cmd = [_azcopy_cmd()]
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
        if self.env:
            env.update(self.env)
        return env

    def _azcopy(self, cmd_name, args, quiet=False):
        cmd = [_azcopy_cmd(), cmd_name] + args
        log.debug("azcopy: %r", cmd)
        try:
            remote_util.subprocess_call(cmd, env=self._cmd_env(), quiet=quiet)
        except subprocess.CalledProcessError as e:
            raise remotelib.RemoteProcessError.for_called_process_error(e)

    def filtered_runs(self, **filters):
        self._sync_runs_meta()
        args = click_util.Args(**filters)
        args.archive = self._runs_dir
        args.remote = None
        args.runs = []
        return runs_impl.runs_for_args(args)

    def delete_runs(self, **opts):
        self._sync_runs_meta()
        args = click_util.Args(**opts)
        args.archive = self._runs_dir
        if args.permanent:
            preview = (
                "WARNING: You are about to permanently delete "
                "the following runs on %s:" % self.name
            )
            confirm = "Permanently delete these runs?"
        else:
            preview = "You are about to delete the following runs on %s:" % self.name
            confirm = "Delete these runs?"
        no_runs_help = "Nothing to delete."

        def delete_f(selected):
            self._delete_runs(selected, args.permanent)
            self._new_meta_id()
            self._sync_runs_meta(force=True)

        try:
            runs_impl.runs_op(
                args,
                None,
                False,
                preview,
                confirm,
                no_runs_help,
                delete_f,
                confirm_default=not args.permanent,
            )
        except SystemExit as e:
            self._reraise_system_exit(e)

    def _reraise_system_exit(self, e, deleted=False):
        if not e.args[0]:
            raise e
        assert len(e.args) == 2, e.args
        exit_code = e.args[1]
        msg = e.args[0].replace(
            "guild runs list",
            "guild runs list %s-r %s" % (deleted and "-d " or "", self.name),
        )
        raise SystemExit(msg, exit_code)

    def _delete_runs(self, runs, permanent):
        for run in runs:
            run_path = self._container_path(*(RUNS_PATH + [run.id]))
            if permanent:
                self._azcopy("remove", [run_path, "--recursive"])
            else:
                raise SystemExit(
                    "non permanent delete is not supported by this remote\n"
                    "Use the '--permanent' with this command and try again.",
                    1,
                )
                deleted_path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
                # TODO: We want a simple move/rename here but it looks
                # like azcopy requires copy+delete. The copy from a
                # blob for some reason requires a SAS token. Stubbing
                # this out for now.
                self._azcopy("copy", [run_path, deleted_path, "--recursive"])
                self._azcopy("remove", [run_path, "--recursive"])

    def _container_path(self, *path_parts):
        all_parts = path_parts if not self.root else (self.root,) + path_parts
        if not all_parts:
            return self.container
        return self.container + "/" + "/".join(all_parts)

    def restore_runs(self, **opts):
        raise SystemExit("this remote does not support restore at this time", 1)
        self._sync_runs_meta()
        args = click_util.Args(**opts)
        args.archive = self._deleted_runs_dir
        preview = "You are about to restore the following runs on %s:" % self.name
        confirm = "Restore these runs?"
        no_runs_help = "Nothing to restore."

        def restore_f(selected):
            self._restore_runs(selected)
            self._new_meta_id()
            self._sync_runs_meta(force=True)

        try:
            runs_impl.runs_op(
                args,
                None,
                False,
                preview,
                confirm,
                no_runs_help,
                restore_f,
                confirm_default=True,
            )
        except SystemExit as e:
            self._reraise_system_exit(e, deleted=True)

    def _restore_runs(self, runs):
        for run in runs:
            deleted_path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
            restored_path = self._container_path(*(RUNS_PATH + [run.id]))
            # TODO: See _delete_runs above. Same problem applies here.
            self._azcopy("copy", [deleted_path, restored_path, "--recursive"])
            self._azcopy("remove", [deleted_path, "--recursive"])

    def purge_runs(self, **opts):
        self._sync_runs_meta()
        args = click_util.Args(**opts)
        args.archive = self._deleted_runs_dir
        preview = (
            "WARNING: You are about to permanently delete "
            "the following runs on %s:" % self.name
        )
        confirm = "Permanently delete these runs?"
        no_runs_help = "Nothing to purge."

        def purge_f(selected):
            self._purge_runs(selected)
            self._new_meta_id()
            self._sync_runs_meta(force=True)

        try:
            runs_impl.runs_op(
                args,
                None,
                False,
                preview,
                confirm,
                no_runs_help,
                purge_f,
                confirm_default=False,
            )
        except SystemExit as e:
            self._reraise_system_exit(e, deleted=True)

    def _purge_runs(self, runs):
        for run in runs:
            path = self._container_path(*(DELETED_RUNS_PATH + [run.id]))
            self._azsync("remove", [path, "--recursive"])

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

    def start(self):
        log.info("Creating S3 bucket %s", self.container)
        try:
            self._azcopy("mb", ["s3://%s" % self.container])
        except remotelib.RemoteProcessError:
            raise remotelib.OperationError()

    def reinit(self):
        self.start()

    def stop(self):
        log.info("Deleting S3 bucket %s", self.container)
        try:
            self._azcopy("rb", ["--force", "s3://%s" % self.container])
        except remotelib.RemoteProcessError:
            raise remotelib.OperationError()

    def get_stop_details(self):
        return (
            "- S3 bucket %s will be deleted - THIS CANNOT BE UNDONE!" % self.container
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
            args.insert[:0] = ["--delete-destination", "true"]
        log.info("Copying %s to %s", run.id, self.name)
        self._azcopy("sync", args)

    def _new_meta_id(self):
        meta_id = _uuid()
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
            args.insert[:0] = ["--delete-destination", "true"]
        log.info("Copying %s from %s", run.id, self.name)
        util.ensure_dir(local_run_dest)
        self._azcopy("sync", args)

    def label_runs(self, **opts):
        raise NotImplementedError("TODO")

    def run_info(self, **opts):
        self._sync_runs_meta()
        args = click_util.Args(**opts)
        args.archive = self._runs_dir
        args.remote = None
        args.private_attrs = False
        runs_impl.run_info(args, None)

    def one_run(self, run_id_prefix):
        raise NotImplementedError("TODO")

    def run_op(self, opspec, flags, restart, no_wait, stage, **opts):
        raise remotelib.OperationNotSupported()

    def watch_run(self, **opts):
        raise remotelib.OperationNotSupported()

    def check(self, **opts):
        raise remotelib.OperationNotSupported()

    def stop_runs(self, **opts):
        raise remotelib.OperationNotSupported()


def _init_env(env_config):
    if isinstance(env_config, dict):
        return env_config
    elif isinstance(env_config, str):
        return _env_from_file(env_config)
    elif env_config is None:
        return {}
    else:
        log.warning("invalid value for remote env %r - ignoring", env_config)
        return {}


def _env_from_file(path):
    if path.lower().endswith(".gpg"):
        env_str = _try_read_gpg(path)
    else:
        env_str = util.try_read(path)
    if not env_str:
        log.warning("cannot read remote env from %s - ignorning", path)
        return {}
    return _decode_env(env_str)


def _try_read_gpg(path):
    path = os.path.expanduser(path)
    cmd = _gpg_cmd() + [path]
    try:
        p = subprocess.Popen(
            cmd, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError as e:
        log.error("cannot decode %s with command '%s' (%s)", path, " ".join(cmd), e)
    else:
        out, err = p.communicate()
        if p.returncode != 0:
            log.error(err.decode(errors="replace").strip())
            return None
        return out.decode(errors="replace")


def _gpg_cmd():
    gpg_env = os.getenv("GPG_CMD")
    if gpg_env:
        return util.shlex_split(gpg_env)
    return ["gpg", "-d"]


def _decode_env(s):
    return dict([_split_env_line(line) for line in s.split("\n")])


def _split_env_line(s):
    parts = s.split("=", 1)
    if len(parts) == 1:
        parts.append("")
    return _strip_export(parts[0]), parts[1]


def _strip_export(s):
    s = s.strip()
    if s.startswith("export "):
        s = s[7:]
    return s


def _azcopy_cmd():
    cmd = util.which("azcopy")
    if not cmd:
        raise remotelib.OperationError(
            "AzCopy is not available\n"
            "Refer to https://docs.microsoft.com/en-us/azure/storage/"
            "common/storage-use-azcopy-v10 for help installing it."
        )
    return cmd


def _join_path(root, *parts):
    path = [part for part in itertools.chain([root], parts) if part not in ("/", "")]
    return "/".join(path)


def _list(d):
    try:
        return os.listdir(d)
    except OSError as e:
        if e.errno != 2:
            raise
        return []


def _ids_for_prefixes(prefixes):
    def strip(s):
        if s.endswith("/"):
            return s[:-1]
        return s

    return [strip(p) for p in prefixes]


def _uuid():
    try:
        return uuid.uuid1().hex
    except ValueError:
        # Workaround https://bugs.python.org/issue32502
        return uuid.uuid4().hex
