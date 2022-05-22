# Copyright 2017-2022 RStudio, PBC
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

import collections
import logging
import re
import os
import subprocess

from guild import util


class UnsupportedRepo(Exception):
    pass


class Scheme:
    def __init__(
        self,
        name,
        commit_cmd,
        commit_pattern,
        commit_ok_errors,
        status_cmd,
        status_pattern,
        status_ok_errors,
    ):
        self.name = name
        self.commit_cmd = commit_cmd
        self.commit_pattern = commit_pattern
        self.commit_ok_errors = commit_ok_errors
        self.status_cmd = status_cmd
        self.status_pattern = status_pattern
        self.status_ok_errors = status_ok_errors


SCHEMES = [
    Scheme(
        "git",
        commit_cmd=["git", "log", "-1", "."],
        commit_pattern=re.compile(r"commit ([a-f0-9]+)"),
        commit_ok_errors=[128],
        status_cmd=["git", "status", "-s"],
        status_pattern=re.compile(r"(.)"),
        status_ok_errors=[],
    )
]

FileStatus = collections.namedtuple("FileStatus", ["status", "path", "renamed_from"])


log = logging.getLogger("guild")


class NoCommit(Exception):
    pass


class CommitReadError(Exception):
    pass


def commit_for_dir(dir):
    """Returns a tuple of commit and workspace status.

    Raises NoCommit if a commit is not available.
    """
    dir = os.path.abspath(dir)
    for scheme in SCHEMES:
        commit = _apply_scheme(
            dir,
            scheme.commit_cmd,
            scheme.commit_pattern,
            scheme.commit_ok_errors,
        )
        if commit is None:
            raise NoCommit(dir)
        status = _apply_scheme(
            dir,
            scheme.status_cmd,
            scheme.status_pattern,
            scheme.status_ok_errors,
        )
        return _format_commit(commit, scheme), _format_status(status)
    raise NoCommit(dir)


def _apply_scheme(repo_dir, cmd_template, pattern, ok_errors):
    cmd = [arg.format(repo=repo_dir) for arg in cmd_template]
    log.debug("vcs scheme cmd for repo %s: %s", repo_dir, cmd)
    try:
        out = subprocess.check_output(
            cmd, cwd=repo_dir, env=os.environ, stderr=subprocess.STDOUT
        )
    except OSError as e:
        if e.errno == 2:
            return None
        raise CommitReadError(e)
    except subprocess.CalledProcessError as e:
        if e.returncode in ok_errors:
            return None
        raise CommitReadError(e, e.output)
    else:
        out = out.decode("ascii", errors="replace")
        log.debug("vcs scheme result: %s", out)
        m = pattern.match(out)
        if not m:
            return None
        return m.group(1)


def _format_commit(commit, scheme):
    return "%s:%s" % (scheme.name, commit)


def _format_status(status):
    return bool(status)


def iter_source_files(dir):
    try:
        return util.try_apply([_try_git_source_iter], dir)
    except util.TryFailed:
        raise UnsupportedRepo(dir) from None


def _try_git_source_iter(dir):
    """Class that conforms to the util.try_apply scheme for iterating source.

    Raises `util.TryFailed` if git does not provide a list of files.
    """
    tracked = _try_git_ls_files(dir, untracked=False)
    untracked = _try_git_ls_files(dir, untracked=True)
    return tracked + untracked


def _try_git_ls_files(dir, untracked=False):
    cmd = ["git", "ls-files"]
    if untracked:
        cmd.extend(["--other", "--exclude-standard"])
    try:
        out = subprocess.check_output(cmd, cwd=dir, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.error("error listing git files (%i)", e.returncode)
            log.error(e.stdout)
        raise util.TryFailed() from None
    else:
        return _parse_git_ls_files(out)


def _parse_git_ls_files(out):
    lines = out.decode("utf-8", errors="ignore").rstrip().split("\n")
    return [path for path in lines if path]


def dir_status(dir):
    try:
        return util.try_apply([_try_git_status], dir)
    except util.TryFailed:
        raise UnsupportedRepo(dir) from None


def _try_git_status(dir):
    cmd = ["git", "status", "-s", "."]
    try:
        out = subprocess.check_output(cmd, cwd=dir, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.error("error listing git files (%i)", e.returncode)
            log.error(e.stdout)
        raise util.TryFailed() from None
    else:
        return _parse_git_status(out)


def _parse_git_status(out):
    lines = out.decode("utf-8", errors="ignore").rstrip().split("\n")
    return [_decode_git_status_line(line) for line in lines if line]


def _decode_git_status_line(status_line):
    status = _normalize_git_file_status(status_line[:2].strip())
    rest = status_line[3:]
    path, renamed_from = _split_git_file_status_path(status, rest)
    return FileStatus(status, path, renamed_from)


def _normalize_git_file_status(status):
    if status == "??":
        return "?"
    return status


def _split_git_file_status_path(status, rest):
    if status == "R":
        return _parse_git_rename(rest)
    else:
        return rest, None


def _parse_git_rename(rest):
    parts = rest.split(" -> ", 1)
    assert len(parts) == 2, parts
    return parts[1], parts[0]
