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

from collections import namedtuple

import errno
import fnmatch
import logging
import os
import shutil

from guild import file_util
from guild import run_manifest


log = logging.getLogger("guild")


class MergeError(Exception):
    pass


class StopMerge(Exception):
    """Raised during a merge to indicate the operation stopped early."""

    def __init__(self, target_file, msg=None):
        super().__init__([target_file, msg])
        self.target_file = target_file
        self.msg = msg


RunMerge = namedtuple(
    "RunMerge",
    [
        "run",
        "target_dir",
        "copy_all",
        "skip_sourcecode",
        "skip_deps",
        "exclude",
        "to_copy",
        "to_skip",
    ],
)

CopyFile = namedtuple(
    "MergeFile",
    [
        "file_type",
        "run_path",
        "target_path",
    ],
)
CopyFile.__doc__ = """
Represents a merge file to be copied.

`file_type` is one of:

  s - source code file
  d - project-local dependency source
  o - 'other' file - i.e. a non-source and not a dependency, likely
      generated by the run
"""

SkipFile = namedtuple(
    "SkipFile",
    [
        "file_type",
        "run_path",
        "target_path",
        "reason",
    ],
)
SkipFile.__doc__ = """
Represents a merge file that is skipped rather than copied.

`file_type` is one of:

  s - source code file
  d - project-local dependency source
  o - 'other' file - i.e. a non-source and not a dependency, likely
      generated by the run

`reason` is a code indicating why the file is skipped.

  x   - path matches a user-provided exclude pattern
  s   - user opted to skip source code files
  d   - user opted to skip dependencies
  npd - file is a non-project dependencies (either from a non-project
        location or from a project-local unpacked archive)
  u   - file is unchanged
  ?   - file from manifest is unknown (not a source code file or
        dependency source)
"""

_ManifestEntry = namedtuple(
    "_ManifestEntry",
    [
        "file_type",
        "run_path",
        "file_hash",
        "source",
        "source_subpath",
    ],
)
_ManifestEntry.__doc__ = """
Represents an entry from the run manifest, which is used to record
known files at the time of run init.

Expected values for `file_type` are 's' and 'd' for source code file
and project-local dependency respectively.
"""


def init_run_merge(
    run,
    target_dir,
    copy_all=False,
    skip_sourcecode=False,
    skip_deps=False,
    exclude=None,
    prefer_nonsource=False,
):
    manifest_index = _init_manifest_index(run)
    merge = RunMerge(
        run,
        target_dir,
        copy_all=copy_all,
        skip_sourcecode=skip_sourcecode,
        skip_deps=skip_deps,
        exclude=exclude,
        to_copy=[],
        to_skip=[],
    )
    _apply_run_files_to_merge(run, manifest_index, merge)
    _prune_overlapping_targets(merge, prefer_nonsource)
    return merge


def _init_manifest_index(run):
    """Returns a dict keyed by run path containing _ManifestEntry items."""
    try:
        manifest = run_manifest.manfiest_for_run(run)
    except FileNotFoundError as e:
        raise MergeError(f"run manifest does not exist for run {run.id}") from e
    else:
        index = {}
        for manifest_entry in manifest:
            index_entry = _manifest_index_entry(manifest_entry, run)
            if not index_entry:
                continue
            index[index_entry.run_path] = index_entry
        return index


def _manifest_index_entry(entry, run):
    if len(entry) not in (4, 5):
        log.warning("unexpected manfiest entry for run %s: %s", run.id, entry)
        return None
    file_type = entry[0]
    run_path = entry[1]
    file_hash = entry[2]
    source = entry[3]
    source_subpath = entry[4] if len(entry) == 5 else None
    return _ManifestEntry(file_type, run_path, file_hash, source, source_subpath)


def _apply_run_files_to_merge(run, manifest_index, merge):
    for run_path in sorted(_iter_run_files(run)):
        _apply_run_file_to_merge(run_path, manifest_index, merge)


def _iter_run_files(run):
    for path in file_util.find(
        run.dir, followlinks=True, includedirs=True, unsorted=True
    ):
        full_path = os.path.join(run.dir, path)
        if os.path.isfile(full_path):
            yield path


def _apply_run_file_to_merge(run_path, manifest_index, merge):
    manifest_entry = manifest_index.get(run_path)
    if manifest_entry:
        _apply_manifest_entry_to_merge(manifest_entry, merge)
    else:
        _apply_unknown_file_to_merge(run_path, merge)


def _apply_manifest_entry_to_merge(entry, merge):
    if entry.file_type == "s":
        _apply_sourcecode_entry(entry, merge)
    elif entry.file_type == "d":
        _apply_dep_entry(entry, merge)
    else:
        log.warning(
            "unknown manifest file type '%s' for run file '%s'",
            entry.file_type,
            entry.run_path,
        )
        _skip_unknown_path(entry.run_path, entry.source, entry.file_type, merge)


def _apply_sourcecode_entry(entry, merge):
    if merge.skip_sourcecode:
        _skip_sourcecode_entry(entry.run_path, entry.source, merge)
    elif _is_excluded_path(entry.source, merge):
        _skip_excluded(entry.run_path, entry.source, entry.file_type, merge)
    elif _is_unchanged(entry.run_path, entry.source, merge):
        _skip_unchanged(entry.run_path, entry.source, entry.file_type, merge)
    else:
        _copy_sourcecode_entry(entry, merge)


def _skip_sourcecode_entry(run_path, target_path, merge):
    merge.to_skip.append(SkipFile("s", run_path, target_path, "s"))


def _is_excluded_path(path, merge):
    if not merge.exclude:
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in merge.exclude)


def _skip_excluded(run_path, target_path, file_type, merge):
    merge.to_skip.append(SkipFile(file_type, run_path, target_path, "x"))


def _is_unchanged(run_path, target_path, merge):
    """Returns True if a run path is unchanged in the target.

    Returns False if the merge is not configured with a target dir
    (i.e. `merge.target_dir` is None.
    """
    dest = os.path.join(merge.target_dir, target_path)
    if not os.path.isfile(dest):
        return False
    src = os.path.join(merge.run.dir, run_path)
    return not file_util.files_differ(src, dest)


def _skip_unchanged(run_path, target_path, file_type, merge):
    merge.to_skip.append(SkipFile(file_type, run_path, target_path, "u"))


def _copy_sourcecode_entry(entry, merge):
    merge.to_copy.append(CopyFile("s", entry.run_path, entry.source))


def _apply_dep_entry(entry, merge):
    if merge.skip_deps:
        _skip_dep_entry(entry, merge)
    else:
        target_path = _target_path_for_dep_entry(entry)
        if target_path:
            if _is_excluded_path(target_path, merge):
                _skip_excluded(entry.run_path, target_path, entry.file_type, merge)
            elif _is_unchanged(entry.run_path, target_path, merge):
                _skip_unchanged(entry.run_path, target_path, entry.file_type, merge)
            else:
                _copy_dep_entry(entry, target_path, merge)
        else:
            _skip_non_project_dep(entry.run_path, merge)


def _skip_dep_entry(entry, merge):
    merge.to_skip.append(
        SkipFile("d", entry.run_path, _target_path_for_dep_entry(entry), "d")
    )


def _target_path_for_dep_entry(entry):
    if not entry.source_subpath and entry.source.startswith("file:"):
        return entry.source[5:]
    return None


def _copy_dep_entry(entry, project_path, merge):
    merge.to_copy.append(CopyFile("d", entry.run_path, project_path))


def _skip_non_project_dep(path, merge):
    merge.to_skip.append(SkipFile("d", path, None, "npd"))


def _skip_unknown_path(run_path, target_path, file_type, merge):
    merge.to_skip.append(SkipFile(file_type, run_path, target_path, "?"))


def _apply_unknown_file_to_merge(run_path, merge):
    if _is_guildfile(run_path):
        return
    # We don't know anything about the file - assume it corresponds to
    # the path in the project for the purpose of mergine.
    target_path = run_path
    if not merge.copy_all:
        _skip_unknown_path(run_path, target_path, "o", merge)
    elif _is_excluded_path(run_path, merge):
        _skip_excluded(run_path, target_path, "o", merge)
    elif _is_unchanged(run_path, target_path, merge):
        _skip_unchanged(run_path, target_path, "o", merge)
    else:
        _copy_other_path(run_path, target_path, merge)


def _is_guildfile(path):
    return path.startswith(".guild")


def _copy_other_path(run_path, target_path, merge):
    merge.to_copy.append(CopyFile("o", run_path, target_path))


def apply_run_merge(merge, pre_copy=None):
    for cf in _sorted_copy_files(merge.to_copy):
        _apply_copy_file_for_merge(cf, merge, pre_copy)


def _sorted_copy_files(files):
    return sorted(files, key=lambda cf: cf.target_path)


def _apply_copy_file_for_merge(cf, merge, pre_copy):
    src = os.path.join(merge.run.dir, cf.run_path)
    dest = os.path.join(merge.target_dir, cf.target_path)
    _apply_pre_copy(pre_copy, merge, cf, src, dest)
    _copy_file(src, dest)


def _apply_pre_copy(pre_copy, merge, cf, src, dest):
    if not pre_copy:
        return
    pre_copy(merge, cf, src, dest)


def _copy_file(src, dest):
    try:
        _shutil_copy(src, dest)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        os.makedirs(os.path.dirname(dest))
        _shutil_copy(src, dest)


def _shutil_copy(src, dest):
    try:
        shutil.copy(src, dest)
    except shutil.SameFileError:
        pass


def _prune_overlapping_targets(merge, prefer_nonsource=False):
    """Removes merge `to_copy` files with overlapping target paths.

    Overlapping targets may occur because Guild supports two categries
    of files for merge: source code and non-source code. Non-source
    code files include dependencies and generated files.

    `merge.files` may be modified as a result of calling this function.

    By default, the pruning prefers source code files over non-source
    code files. In the default case, when a target path exists both as
    source code and as non-source code, the source code file is
    retained and the non-source code file is pruned.

    To prefer non-source code files over source code files, specify
    `prefer_nonsource=True`.
    """
    source_lookup = {cf.target_path for cf in merge.to_copy if cf.file_type == "s"}
    nonsource_lookup = {cf.target_path for cf in merge.to_copy if cf.file_type != "s"}
    merge.to_copy[:] = [
        cf
        for cf in merge.to_copy
        if _keep_for_prune_overlapping(
            cf,
            source_lookup,
            nonsource_lookup,
            prefer_nonsource,
        )
    ]


def _keep_for_prune_overlapping(cf, source_lookup, nonsource_lookup, prefer_nonsource):
    return not (
        cf.target_path in source_lookup and cf.target_path in nonsource_lookup
    ) or (cf.file_type != "s" if prefer_nonsource else cf.file_type == "s")
