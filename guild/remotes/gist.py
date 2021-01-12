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
import pprint
import shutil
import subprocess
import sys
import zipfile

from guild import remote as remotelib
from guild import remote_util
from guild import util

from . import meta_sync

log = logging.getLogger("guild.remotes.gist")


class NoSuchGist(remotelib.OperationError):
    pass


class MissingRequiredEnv(remotelib.OperationError):
    pass


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
    if len(parts) == 1:
        try:
            return _required_gist_user_env({}), parts[0]
        except MissingRequiredEnv as e:
            raise remotelib.InvalidRemoteSpec(str(e))
    return parts


def _required_gist_user_env(env):
    try:
        return _required_env("GIST_USER", [env, os.environ])
    except KeyError:
        raise MissingRequiredEnv(
            "gist remotes must be specified as USER/GIST_NAME if GIST_USER "
            "environment variable is not defined"
        )


def _required_env(name, sources):
    for src in sources:
        try:
            return src[name]
        except KeyError:
            pass
    raise KeyError(name)


class GistRemote(meta_sync.MetaSyncRemote):
    def __init__(self, name, config):
        self.name = name
        self.user = config["user"]
        self.gist_name = config["gist-name"]
        self._gist_readme_name = _gist_readme_name(self.gist_name)
        self.local_env = remote_util.init_env(config.get("local-env"))
        self.local_sync_dir = meta_sync.local_meta_dir(
            _remote_full_name(self.user, self.gist_name), ""
        )
        self._local_gist_repo = os.path.join(self.local_sync_dir, "gist")
        runs_dir = os.path.join(self.local_sync_dir, "runs")
        super(GistRemote, self).__init__(runs_dir, None)

    def status(self, verbose=False):
        remote_util.remote_activity("Getting %s status", self.name)
        gist = self._repo_gist()
        sys.stdout.write("%s (gist %s) is available\n" % (self.name, gist["id"]))
        if verbose:
            sys.stdout.write(pprint.pformat(gist))
            sys.stdout.write("\n")

    def start(self):
        remote_util.remote_activity("Getting %s status", self.name)
        try:
            gist = self._repo_gist()
        except NoSuchGist:
            log.info("Creating gist")
            gist = self._create_gist()
            log.info(
                "Created %s (gist %s) for user %s",
                self.name,
                gist["id"],
                self.user,
            )
            self._sync_runs_meta()
        else:
            raise remotelib.OperationError(
                "%s (gist %s) already exists for user %s"
                % (self.name, gist["id"], self.user)
            )

    def stop(self):
        self._delete_gist()
        self._clear_gist_cache()

    def _delete_gist(self):
        gist = self._repo_gist()
        log.info("Deleting gist %s", gist["id"])
        _delete_gist(gist, self.local_env)

    def _clear_gist_cache(self):
        log.info("Clearning local cache")
        log.debug("deleting %s", self.local_sync_dir)
        util.ensure_safe_rmtree(self.local_sync_dir)

    def stop_details(self):
        remote_util.remote_activity("Getting %s status", self.name)
        try:
            gist = self._repo_gist()
        except NoSuchGist:
            return None
        else:
            return "gist %s will be deleted - THIS CANNOT BE UNDONE!" % gist["id"]

    def _sync_runs_meta(self, force=False):
        remote_util.remote_activity("Refreshing run info for %s" % self.name)
        self._ensure_local_gist_repo()
        self._sync_runs_meta_for_gist(force)

    def _ensure_local_gist_repo(self):
        if _is_git_repo(self._local_gist_repo):
            log.debug("gist local repo found at %s", self._local_gist_repo)
            return
        log.debug("initializing gist local repo at %s", self._local_gist_repo)
        gist = self._repo_gist()
        _sync_gist_repo(gist, self._local_gist_repo, self.local_env)

    def _repo_gist(self):
        gist = _find_gist_with_file(self.user, self._gist_readme_name, self.local_env)
        if not gist:
            raise NoSuchGist(
                "cannot find gist remote '%s' (denoted by the file '%s') for user %s\n"
                "If the gist is private, you must specify a valid access token with "
                "GIST_ACCESS_TOKEN.\nFor more information see "
                "https://my.guild.ai/docs/gists."
                % (self.gist_name, self._gist_readme_name, self.user)
            )
        return gist

    def _sync_runs_meta_for_gist(self, force):
        try:
            _pull_gist_repo(self._local_gist_repo, self.local_env)
        except NoSuchGist:
            self._clear_gist_cache()
        else:
            git_commit = self._gist_repo_current_commit()
            if not force and self._meta_current(git_commit):
                return
            _refresh_runs_meta(
                self._local_gist_repo,
                self._runs_dir,
                git_commit,
                self.local_sync_dir,
            )

    def _meta_current(self, git_commit):
        return meta_sync.meta_current(self.local_sync_dir, lambda: git_commit)

    def _gist_repo_current_commit(self):
        return _git_current_commit(self._local_gist_repo)

    def _delete_runs(self, runs, permanent):
        assert permanent  # gist remotes only support permanent delete
        _delete_gist_runs(runs, self._local_gist_repo, self._runs_dir)
        _commit_and_push_gist_repo_for_delete(
            self._local_gist_repo,
            _delete_commit_msg(),
            self.local_env,
            self.name,
        )

    def _restore_runs(self, runs):
        raise NotImplementedError()

    def _purge_runs(self, runs):
        raise NotImplementedError()

    def push(self, runs, delete=False):
        self._ensure_synced_gist_repo()
        _export_runs_to_gist_archives(runs, self._local_gist_repo)
        _commit_and_push_gist_repo_for_push(
            self._local_gist_repo,
            _push_commit_msg(),
            self.local_env,
            self.name,
        )
        self._sync_runs_meta_for_gist(True)

    def _ensure_synced_gist_repo(self):
        try:
            self._sync_runs_meta()
        except NoSuchGist:
            self._init_gist_repo()

    def _init_gist_repo(self):
        gist = self._create_gist()
        _sync_gist_repo(gist, self._local_gist_repo, self.local_env)

    def _create_gist(self):
        return _create_gist(self.gist_name, self._gist_readme_name, self.local_env)

    def pull(self, runs, delete=False):
        from guild import var

        # That we have `runs` means we've sync'd runs meta. "Meta" in
        # this case also contains the runs themselves as zip
        # archives. At this point we need only extract the run
        # archives to the runs dir.
        _extract_runs(runs, self._local_gist_repo, var.runs_dir(), self.name)


def _remote_full_name(user, gist_name):
    return "gist-%s-%s" % (user, gist_name)


def _gist_readme_name(gist_name):
    return "[Guild AI] %s" % _ensure_md_ext(gist_name)


def _ensure_md_ext(s):
    if s.lower().endswith(".md"):
        return s
    return s + ".md"


def _find_gist_with_file(user, filename, env):
    import requests  # expensive

    page = 1
    url = "https://api.github.com/users/%s/gists" % user
    while True:
        resp = requests.get(
            url,
            params={"page": page, "per_page": 100},
            headers=_github_auth_headers(env),
        )
        gists = resp.json()
        if not gists:
            return None
        for gist in gists:
            for name in gist["files"]:
                if name == filename:
                    return gist
        page += 1


def _github_auth_headers(env):
    try:
        access_token = _required_gist_access_token(env)
    except MissingRequiredEnv:
        return {}
    else:
        return {"Authorization": "token %s" % access_token}


def _sync_gist_repo(gist, local_repo, env):
    repo_url = _gist_repo_url(gist, env)
    if _is_git_repo(local_repo):
        _pull_gist_repo(local_repo, env)
    else:
        _clone_gist_repo(repo_url, local_repo, env)


def _gist_repo_url(gist, env):
    if _gist_urltype(env) == "ssh":
        return "git@gist.github.com:%s.git" % gist["id"]
    else:
        return gist["git_pull_url"]


def _gist_urltype(env):
    try:
        return _required_env("GIST_URLTYPE", [env, os.environ])
    except KeyError:
        return None


def _clone_gist_repo(repo_url, local_repo, env):
    cmd = [_git_cmd(), "clone", "--quiet", repo_url, local_repo]
    log.debug("cloning %s to %s", repo_url, local_repo)
    _subprocess_tty(cmd, extra_env=env)


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
    cmd = [_git_cmd(), "-C", local_repo, "pull", "--quiet", "--rebase"]
    log.debug("pulling for %s", local_repo)
    code = _subprocess_tty(cmd, extra_env=env, allowed_returncodes=(0, 1))
    if code == 1:
        raise NoSuchGist()


def _refresh_runs_meta(gist_repo, runs_dir, meta_id, local_sync_dir):
    for archive in _run_archives(gist_repo):
        _unpack_meta(archive, runs_dir)
    meta_sync.write_local_meta_id(meta_id, local_sync_dir)


def _run_archives(dir):
    for name in os.listdir(dir):
        if _is_guild_run(name):
            yield os.path.join(dir, name)


def _is_guild_run(name):
    return name.startswith("guildai-run-") and name.endswith(".zip")


def _unpack_meta(archive, runs_dir):
    log.debug("unpacking %s meta to %s", archive, runs_dir)
    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            if _is_meta_file(name):
                zf.extract(name, runs_dir)


def _is_meta_file(name):
    return (
        name.endswith(".guild/opref")
        or "/.guild/attrs/" in name
        or "/.guild/LOCK" in name
    )


def _is_git_repo(dir):
    return os.path.exists(os.path.join(dir, ".git"))


def _git_current_commit(git_repo):
    if not _is_git_repo(git_repo):
        return None
    cmd = [_git_cmd(), "-C", git_repo, "log", "-1", "--format=%H"]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode("utf-8").strip()


def _extract_runs(runs, archive_dir, dest_dir, gist_name):
    for run in runs:
        archive = os.path.join(archive_dir, _run_archive_filename(run.id))
        if not os.path.exists(archive):
            log.error(
                "%s archive for gist does not exist (%s), skipping", run.id, archive
            )
            continue
        log.info("Copying %s from %s", run.id, gist_name)
        _replace_run(archive, run.id, dest_dir)


def _run_archive_filename(run_id):
    return "guildai-run-%s.zip" % run_id


def _replace_run(archive, run_id, dest_dir):
    with util.TempDir("guild-gist-run-") as tmp:
        _extract_archive(archive, tmp.path)
        extracted_run_dir = _validate_extracted_run(tmp.path, run_id, archive)
        dest_run_dir = os.path.join(dest_dir, run_id)
        _replace_run_dir(dest_run_dir, extracted_run_dir)


def _extract_archive(archive, dest_dir):
    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            zf.extract(name, dest_dir)


def _validate_extracted_run(dir, run_id, archive):
    # RUN_DIR/.guild/opref is required for a run.
    extracted_run_dir = os.path.join(dir, run_id)
    opref_path = os.path.join(extracted_run_dir, ".guild", "opref")
    if not os.path.exists(opref_path):
        log.error("%s does not contain expected run %s", archive, run_id)
        raise remotelib.OperationError("invalid run archive in gist")
    return extracted_run_dir


def _replace_run_dir(run_dir, src_dir):
    log.debug("moving %s to %s", src_dir, run_dir)
    util.ensure_safe_rmtree(run_dir)
    shutil.move(src_dir, run_dir)


def _create_gist(gist_remote_name, gist_readme_name, env):
    import requests

    access_token = _required_gist_access_token(env)
    data = {
        "accept": "application/vnd.github.v3+json",
        "description": "Guild AI Repository",
        "public": True,
        "files": {
            gist_readme_name: {
                "filename": gist_readme_name,
                "type": "text/markdown",
                "language": "Markdown",
                "content": _gist_readme_content(gist_remote_name),
            }
        },
    }
    headers = {
        "Authorization": "token %s" % access_token,
    }
    resp = requests.post("https://api.github.com/gists", json=data, headers=headers)
    if resp.status_code not in (200, 201):
        raise remotelib.OperationError(
            "error creating gist: (%i) %s" % (resp.status_code, resp.text)
        )
    return resp.json()


def _required_gist_access_token(env):
    try:
        return _required_env("GIST_ACCESS_TOKEN", [env, os.environ])
    except KeyError:
        raise MissingRequiredEnv(
            "missing required environment variable GIST_ACCESS_TOKEN\n"
            "This operation requires a GitHub personal access token for "
            "creating gists.\n"
            "See https://my.guild.ai/docs/gists for more information."
        )


def _gist_readme_content(remote_name):
    return (
        "This is a Guild AI runs repository. To access runs, "
        "[install Guild AI](https://guild.ai/install) and run `guild pull gist:%s`. "
        "For more information about Guild AI Gist based repositories, see "
        "[Guild AI - Gists](https://my.guild.ai/docs/gist)." % remote_name
    )


def _export_runs_to_gist_archives(runs, gist_repo):
    with util.TempDir("guild-runs-export-") as tmp:
        archives = [_run_export_archive(run, tmp.path) for run in runs]
        _export_runs(zip(runs, archives))
        for archive_src in archives:
            archive_dest = os.path.join(gist_repo, os.path.basename(archive_src))
            util.ensure_deleted(archive_dest)
            shutil.move(archive_src, archive_dest)


def _run_export_archive(run, export_dir):
    return os.path.join(export_dir, _run_archive_filename(run.id))


def _export_runs(runs_with_dest):
    from guild import run_util

    for run, dest in runs_with_dest:
        log.info("Compressing %s", run.id)
        run_util.export_runs([run], dest, copy_resources=False, quiet=True)


def _push_commit_msg():
    import guild

    return "`guild push` by %s@%s with version %s" % (
        util.user(),
        util.hostname(),
        guild.version(),
    )


def _commit_and_push_gist_repo_for_push(repo, commit_msg, env, remote_name):
    _git_add_all(repo, env)
    try:
        _git_commit(repo, commit_msg, env)
    except _NoChanges:
        pass
    log.info("Copying runs to %s", remote_name)
    _git_push(repo, env)


def _git_add_all(local_repo, env, update=False):
    cmd = [_git_cmd(), "-C", local_repo, "add", "."]
    if update:
        cmd.append("-u")
    log.debug("adding files for %s", local_repo)
    _subprocess_quiet(cmd, extra_env=env)


class _NoChanges(Exception):
    pass


def _git_commit(local_repo, msg, env):
    cmd = [_git_cmd(), "-C", local_repo, "commit", "-m", msg]
    log.debug("commiting for %s", local_repo)
    result = _subprocess_quiet(cmd, extra_env=env, allowed_returncodes=(0, 1))
    if result == 1:
        raise _NoChanges()


def _git_push(local_repo, env):
    cmd = [_git_cmd(), "-C", local_repo, "push", "--quiet"]
    env = _maybe_askpass(env, local_repo)
    log.debug("pushing for %s", local_repo)
    _subprocess_tty(cmd, extra_env=env)


def _maybe_askpass(env, local_repo):
    if not _gist_access_token_defined(env):
        return
    askpass_path = _maybe_gist_access_token_script(local_repo)
    if not askpass_path:
        return env
    env = dict(env)
    env["GIT_ASKPASS"] = askpass_path
    return env


def _gist_access_token_defined(env):
    try:
        _required_env("GIST_ACCESS_TOKEN", [env, os.environ])
    except KeyError:
        return False
    else:
        return True


def _maybe_gist_access_token_script(local_repo):
    if util.get_platform() == "Windows":
        return None
    script_path = _gist_access_token_script(local_repo)
    if os.path.exists(script_path):
        return script_path
    _write_gist_access_token_script(script_path)
    return script_path


def _gist_access_token_script(local_repo):
    return os.path.join(local_repo, ".git", "gist-access-token")


def _write_gist_access_token_script(path):
    with open(path, "w") as f:
        f.write("echo $GIST_ACCESS_TOKEN\n")
    util.make_executable(path)


def _delete_gist(gist, env):
    import requests

    access_token = _required_gist_access_token(env)
    data = {
        "accept": "application/vnd.github.v3+json",
        "gist_id": gist["id"],
    }
    headers = {
        "Authorization": "token %s" % access_token,
    }
    resp = requests.delete(
        "https://api.github.com/gists/%s" % gist["id"], json=data, headers=headers
    )
    if resp.status_code not in (200, 204):
        raise remotelib.OperationError(
            "error creating gist: (%i) %s" % (resp.status_code, resp.text)
        )


def _delete_gist_runs(runs, gist_repo, runs_dir):
    for run in runs:
        log.info("Deleting %s", run.id)
        _delete_gist_repo_run_archive(gist_repo, run.id)
        _delete_run(run, runs_dir)


def _delete_gist_repo_run_archive(gist_repo, run_id):
    run_archive = os.path.join(gist_repo, _run_archive_filename(run_id))
    log.debug("deleting %s", run_archive)
    util.ensure_deleted(run_archive)


def _delete_run(run, runs_dir):
    run_dir = os.path.join(runs_dir, run.id)
    log.debug("deleting %s", run_dir)
    util.ensure_safe_rmtree(run_dir)


def _commit_and_push_gist_repo_for_delete(repo, commit_msg, env, remote_name):
    _git_add_all(repo, env, update=True)
    try:
        _git_commit(repo, commit_msg, env)
    except _NoChanges:
        log.info("Nothing to update for %s - gist is up-to-date", remote_name)
    else:
        log.info("Updating runs on %s", remote_name)
        _git_push(repo, env)


def _delete_commit_msg():
    import guild

    return "`guild runs rm` by %s@%s with version %s" % (
        util.user(),
        util.hostname(),
        guild.version(),
    )


def _subprocess_tty(cmd, extra_env, allowed_returncodes=(0,)):
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    log.debug("%r", cmd)
    p = subprocess.Popen(cmd, env=env)
    p.wait()
    if p.returncode not in allowed_returncodes:
        log.debug("exit code for %r is %i", cmd, p.returncode)
        raise SystemExit("error running %s - see above for details" % cmd[0])
    return p.returncode


def _subprocess_quiet(cmd, extra_env, allowed_returncodes=(0,)):
    log.debug("%r", cmd)
    return remote_util.subprocess_call(
        cmd,
        extra_env=extra_env,
        quiet=True,
        allowed_returncodes=allowed_returncodes,
    )
