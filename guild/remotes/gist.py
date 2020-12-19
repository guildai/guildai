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
import zipfile

import requests

from guild import log as loglib
from guild import remote as remotelib
from guild import remote_util
from guild import util

from . import meta_sync

log = logging.getLogger("guild.remotes.gist")


class GistRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return GistRemote(name, config)

    def remote_for_spec(self, spec):
        name = "gist:%s" % spec
        user, gist_name = _parse_spec(spec)
        config = remotelib.RemoteConfig(
            {
                "user": user,
                "gist-name": gist_name,
            }
        )
        return GistRemote(name, config)


def _parse_spec(spec):
    parts = spec.split("/", 1)
    if len(parts) != 2:
        raise remotelib.InvalidRemoteSpec(
            "gist remotes must be specified as USER/GIST_NAME"
        )
    return parts


class GistRemote(meta_sync.MetaSyncRemote):
    def __init__(self, name, config):
        self.name = name
        self.user = config["user"]
        self.gist_name = config["gist-name"]
        self._gist_readme_name = _gist_readme_name(self.gist_name)
        self.local_env = remote_util.init_env(config.get("local-env"))
        self.local_sync_dir = meta_sync.local_meta_dir(name, "")
        self._local_gist_repo = os.path.join(self.local_sync_dir, "gist")
        runs_dir = os.path.join(self.local_sync_dir, "runs")
        super(GistRemote, self).__init__(runs_dir, None)

    def _sync_runs_meta(self, force=False):
        gist = self._repo_gist()
        if not gist:
            return
        _sync_gist_repo(gist, self._local_gist_repo, self.local_env)
        _refresh_runs_meta(self._local_gist_repo, self._runs_dir)

    def _repo_gist(self):
        return _find_gist_with_file(self.user, self._gist_readme_name)

    def _delete_runs(self, runs, permanent):
        assert False

    def _restore_runs(self, runs):
        assert False

    def _purge_runs(self, runs):
        assert False

    def push(self, runs, delete=False):
        for run in runs:
            self._push_run(run, delete)
            self._new_meta_id()
        self._sync_runs_meta(force=True)

    def _push_run(self, run, delete):
        print("Somehow push run %s to a gist %s" % (run.id, self.name, delete))

    def _new_meta_id(self):
        pass

    def pull(self, runs, delete=False):
        for run in runs:
            self._pull_run(run, delete)

    def label_runs(self, **opts):
        raise remotelib.OperationNotSupported()  # TODO

    def run_op(self, opspec, flags, restart, no_wait, stage, **opts):
        raise remotelib.OperationNotSupported()

    def watch_run(self, **opts):
        raise remotelib.OperationNotSupported()

    def check(self, **opts):
        raise remotelib.OperationNotSupported()

    def stop_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def cat(self, **opts):
        raise remotelib.OperationNotSupported()

    def comment_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def diff_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def list_files(self, **opts):
        raise remotelib.OperationNotSupported()

    def one_run(self, run_id_prefix):
        raise remotelib.OperationNotSupported()

    def tag_runs(self, **opts):
        raise remotelib.OperationNotSupported()

    def reinit(self):
        raise remotelib.OperationNotSupported()

    def stop(self):
        raise remotelib.OperationNotSupported()

    def status(self, verbose=False):
        raise remotelib.OperationNotSupported()

    def start(self):
        raise remotelib.OperationNotSupported()


def _gist_readme_name(gist_name):
    return "[Guild AI] %s" % _ensure_md_ext(gist_name)


def _ensure_md_ext(s):
    if s.lower().endswith(".md"):
        return s
    return s + ".md"


def _find_gist_with_file(user, filename):
    page = 1
    url = "https://api.github.com/users/%s/gists" % user
    while True:
        resp = requests.get(url, params={"page": page, "per_page": 100})
        gists = resp.json()
        if not gists:
            return None
        for gist in gists:
            for name in gist["files"]:
                if name == filename:
                    return gist
        page += 1


def _sync_gist_repo(gist, local_repo, env):
    repo_url = _gist_repo_url(gist)
    if not os.path.exists(local_repo):
        _clone_gist_repo(repo_url, local_repo, env)
    else:
        _pull_gist_repo(local_repo, env)


def _gist_repo_url(gist):
    # Use ssh to interface with gist repo
    return "git@gist.github.com:%s.git" % gist["id"]


def _clone_gist_repo(repo_url, local_repo, env):
    cmd = [_git_cmd(), "clone", repo_url, local_repo]
    log.info(loglib.dim("Synchronizing runs with gist.github.com"))
    remote_util.subprocess_call(cmd, extra_env=env, quiet=True)


def _git_cmd():
    cmd = util.which("git")
    if not cmd:
        raise remotelib.OperationError(
            "git command is not available\n"
            "Refer to https://git-scm.com/book/en/v2/Getting-Started-Installing-Git "
            "for help installing it."
        )
    return cmd

def _pull_gist_repo(local_repo, env):
    cmd = [_git_cmd(), "-C", local_repo, "pull", "--rebase"]
    log.info(loglib.dim("Synchronizing runs with gist.github.com"))
    remote_util.subprocess_call(cmd, extra_env=env, quiet=True)


def _refresh_runs_meta(gist_repo, runs_dir):
    for archive in _run_archives(gist_repo):
        _unpack_meta(archive, runs_dir)


def _run_archives(dir):
    for name in os.listdir(dir):
        if name.endswith(".run.zip"):
            yield os.path.join(dir, name)


def _unpack_meta(archive, runs_dir):
    log.debug("unpacking %s meta to %s", archive, runs_dir)
    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            if _is_meta_file(name):
                zf.extract(name, runs_dir)


def _is_meta_file(name):
    return (
        name.endswith(".guild/opref") or
        "/.guild/attrs/" in name or
        "/.guild/LOCK" in name
    )
