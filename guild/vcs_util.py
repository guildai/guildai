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

from guild.file_util import FileSelectRule


class UnsupportedRepo(Exception):
    pass


class NoVCS(Exception):
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

FileStatus = collections.namedtuple("FileStatus", ["status", "path", "orig_path"])
FileStatus.__doc__ = """
Represents a file in the result of `status()`.

`status` is a two character status code. This follows the git
convention as documented in `git status --help` with the exception
that an empty space char (' ') in the git spec becomes an underscore
char ('_') in this spec.

  - _ = unmodified
  - M = modified
  - A = added
  - D = deleted
  - R = renamed
  - C = copied
  - U = updated but unmerged

    X          Y     Meaning
    -------------------------------------------------
    _        [AMD]   not updated
    M        [ MD]   updated in index
    A        [ MD]   added to index
    D                deleted from index
    R        [ MD]   renamed in index
    C        [ MD]   copied in index
    [MARC]      _    index and work tree matches
    [ MARC]     M    work tree changed since index
    [ MARC]     D    deleted in work tree
    [ D]        R    renamed in work tree
    [ D]        C    copied in work tree
    -------------------------------------------------
    D           D    unmerged, both deleted
    A           U    unmerged, added by us
    U           D    unmerged, deleted by them
    U           A    unmerged, added by them
    D           U    unmerged, deleted by us
    A           A    unmerged, both added
    U           U    unmerged, both modified
    -------------------------------------------------
    ?           ?    untracked
    !           !    ignored

"""

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
        raise CommitReadError(e) from e
    except subprocess.CalledProcessError as e:
        if e.returncode in ok_errors:
            return None
        raise CommitReadError(e, e.output) from e
    else:
        out = out.decode("ascii", errors="replace")
        log.debug("vcs scheme result: %s", out)
        m = pattern.match(out)
        if not m:
            return None
        return m.group(1)


def _format_commit(commit, scheme):
    return f"{scheme.name}:{commit}"


def _format_status(status):
    return bool(status)


def ls_files(dir):
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
    return util.split_lines(out.decode("utf-8", errors="ignore"))


def status(dir, ignored=False):
    try:
        return util.try_apply([_try_git_status], dir, ignored)
    except util.TryFailed:
        raise UnsupportedRepo(dir) from None


def _try_git_status(dir, ignored):
    ignored_args = ["--ignored=matching"] if ignored else []
    cmd = ["git", "status", "--short", "--renames"] + ignored_args + ["."]
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
    lines = util.split_lines(out.decode("utf-8", errors="ignore"))
    return [_decode_git_status_line(line) for line in lines]


def _decode_git_status_line(status_line):
    status = _status_code_for_git_status_line(status_line)
    rest = status_line[3:]
    path, orig_path = _split_git_file_status_path(rest)
    return FileStatus(status, path, orig_path)


def _status_code_for_git_status_line(status_line):
    """Returns the XY status git status.

    Git status char ' ' (empty space) is replaced with an underscore
    per the MergeFile status spec above.

    See `git status --help` for details.

    """
    assert len(status_line) >= 2, status_line
    return status_line[:2].replace(" ", "_")


def _split_git_file_status_path(path):
    parts = path.split(" -> ", 1)
    if len(parts) == 2:
        return parts[1], parts[0]
    return parts[0], None


def project_select_rules(project_dir):
    # Only supporting Git based rules
    return git_project_select_rules(project_dir)


def git_project_select_rules(project_dir):
    git_ignored = _git_ls_ignored(project_dir, extended_patterns_file=".guildignore")
    ignored_dirs = _dirs_for_git_ignored(git_ignored, project_dir)
    return [
        # Ignore directories first as an optimization
        FileSelectRule(False, [".git"] + ignored_dirs, "dir"),
        # Git ignore select selects everything that isn't ignored -
        # this must be placed before rules that exclude patterns
        _GitignoreSelectRule(git_ignored),
        FileSelectRule(False, [".git*", ".guildignore"]),
    ]


def _git_ls_ignored(cwd, extended_patterns_file=None):
    cmd = _git_ls_cmd(extended_patterns_file)
    log.debug("cmd for ls ignored in %s: %s", cwd, cmd)
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.returncode not in (128,):
            # 128: not a git repo -> ignore
            log.warning(
                "error listing ignored files (%i): %s",
                e.returncode,
                e.output.decode(),
            )
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.error(e.stdout)
        raise NoVCS(cwd, (e.returncode, e.stdout)) from None
    else:
        return _parse_git_ls_files(out)


def _git_ls_cmd(extended_patterns_file):
    # `--directory` is important here to avoid listing potentially
    # huge numbers of ignored files in directories. This is also
    # relied upon downstream by `_dirs_for_git_ignored()` to list
    # ignored directories that can be skipped by Guild's select rules
    # as a substantial performance optimization.
    cmd = ["git", "ls-files", "-ioc", "--exclude-standard", "--directory"]
    if extended_patterns_file:
        cmd.extend(_exclude_args_for_patterns_file(extended_patterns_file))
    return cmd


def _exclude_args_for_patterns_file(patterns_file):
    return [
        arg
        for pattern in _exclude_patterns_file_entries(patterns_file)
        for arg in ["-x", pattern]
    ]


def _exclude_patterns_file_entries(src):
    try:
        f = open(src)
    except FileNotFoundError:
        return []
    else:
        with f:
            lines = [line.strip() for line in f]
        return [line for line in lines if line and not line.startswith("#")]


def _dirs_for_git_ignored(ignored, root_dir):
    return [
        _strip_trailing_slash(path)
        for path in ignored
        if os.path.isdir(os.path.join(root_dir, path))
    ]


def _strip_trailing_slash(path):
    return path[:-1] if path[-1:] in ("/", "\\") else path


class _GitignoreSelectRule(FileSelectRule):
    """Higher order selection rule using git ignored files.

    This is a 'select everything except ignored' rule and can be used
    in place of a select '*' select rule - with the exception that git
    ignored files are not selected.
    """

    def __init__(self, ignored):
        super().__init__(True, [])
        self.ignored = set(ignored)

    def __str__(self):
        return "gitignore + guildignore patterns"

    def test(self, _src_root, relpath):
        # This is a 'select everything except ignored' rule so we
        # return `True` to select anything that isn't in our list of
        # ignored. This could alternatively be a `False` for anything
        # in ignored, but this would require an explicit select '*'
        # rule to precede it.
        if relpath not in self.ignored:
            return True, None
        return None, None
