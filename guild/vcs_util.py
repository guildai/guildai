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

import logging
import re
import os
import subprocess

import six

from guild import util


class UnsupportedRepo(Exception):
    pass


class Scheme(object):
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
        return util.try_apply([_TryGitSourceIter], dir)
    except util.TryFailed:
        six.raise_from(UnsupportedRepo(dir), None)


class _TryGitSourceIter:
    """Class that conforms to the util.try_apply scheme for iterating source.

    Raises `util.TryFailed` in the contructor
    """

    def __init__(self, dir):
        self._dir = dir
        self._ls_files = _try_ls_files(dir)

    def __iter__(self):
        for path in self._ls_files:
            if path:
                yield path
        for path in _try_ls_files(self._dir, untracked=True):
            if path:
                yield path


def _try_ls_files(dir, untracked=False):
    cmd = ["git", "ls-files"]
    if untracked:
        cmd.extend(["--other", "--exclude-standard"])
    p = subprocess.Popen(cmd, cwd=dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _err = p.communicate()
    if p.returncode != 0:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.error("error listing git files (%i)", p.returncode)
            log.error(out)
        raise util.TryFailed()
    return out.decode("utf-8", errors="ignore").rstrip().split("\n")
