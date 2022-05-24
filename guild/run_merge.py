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
import errno
import fnmatch
import os
import shutil

from guild import file_util
from guild import run_manifest


class MergeError(Exception):
    pass


class StopMerge(Exception):
    """Raised during a merge to indicate the operation stopped early."""

    def __init__(self, target_file, msg=None):
        super(StopMerge, self).__init__([target_file, msg])
        self.target_file = target_file
        self.msg = msg


MergeFile = collections.namedtuple("MergeFile", ["type", "run_path", "target_path"])


class RunMerge:
    def __init__(
        self,
        run,
        skip_sourcecode=False,
        skip_deps=False,
        skip_generated=False,
        exclude=None,
        files=None,
    ):
        self.run = run
        self.skip_sourcecode = skip_sourcecode
        self.skip_deps = skip_deps
        self.skip_generated = skip_generated
        self.exclude = exclude
        self.files = files if files is not None else _init_merge_files(self)


def _init_merge_files(merge):
    files = []
    manifest_index = _manifest_index(merge.run)
    for path in _iter_run_files(merge.run):
        _handle_run_file_for_merge(path, merge, manifest_index, files)
    return files


def _manifest_index(run):
    try:
        m = run_manifest.manfiest_for_run(run)
    except FileNotFoundError:
        raise MergeError(f"run manifest does not exist for run {run.id}")
    else:
        return _index_for_manifest(m)


def _index_for_manifest(m):
    index = {}
    for args in m:
        _apply_manifest_entry_to_index(args, index)
    return index


def _apply_manifest_entry_to_index(args, index):
    if args[0] == "s":
        _apply_sourcecode_entry_to_index(args, index)
    elif args[0] == "d":
        _apply_dep_entry_to_index(args, index)


def _apply_sourcecode_entry_to_index(args, index):
    run_path, _hash_arg, target_path = args[1:]
    index[run_path] = MergeFile("s", run_path, target_path)


def _apply_dep_entry_to_index(args, index):
    if not _is_project_local_dep_entry(args):
        return
    run_path, _hash_arg, target_path = args[1:]
    index[run_path] = MergeFile("d", run_path, target_path)


def _is_project_local_dep_entry(args):
    # Project local files are logged in the run manifst as ['d',
    # run_path, hash, project_path]. See
    # `guild.run_manifest.resolved_source_args()` for details.
    return len(args) == 4


def _iter_run_files(run):
    for path in file_util.find(
        run.dir, followlinks=True, includedirs=True, unsorted=True
    ):
        full_path = os.path.join(run.dir, path)
        if os.path.isfile(full_path):
            yield path


def _handle_run_file_for_merge(run_path, merge, manifest_index, files):
    merge_file = manifest_index.get(run_path) or _maybe_generated_merge_file(run_path)
    if merge_file and not _merge_file_excluded(merge_file, merge):
        files.append(merge_file)


def _maybe_generated_merge_file(run_path):
    return MergeFile("g", run_path, run_path) if not _is_guild_path(run_path) else None


def _is_guild_path(path):
    return path.startswith(".guild")


def _merge_file_excluded(merge_file, merge):
    type = merge_file.type
    return (
        (type == "s" and merge.skip_sourcecode)
        or (type == "d" and merge.skip_deps)
        or (type == "g" and merge.skip_generated)
        or _path_excluded(merge_file.target_path, merge.exclude)
    )


def _path_excluded(path, exclude_patterns):
    if not exclude_patterns:
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in exclude_patterns)


def apply_run_merge(merge, target_dir, pre_copy=None):
    run_dir = merge.run.dir
    for mf in _sorted_merge_files_for_apply(merge.files):
        src = os.path.join(run_dir, mf.run_path)
        dest = os.path.join(target_dir, mf.target_path)
        if pre_copy:
            try:
                pre_copy(merge, mf, src, dest)
            except StopMerge:
                break
        _copy_file(src, dest)


def _sorted_merge_files_for_apply(merge_files):
    return sorted(merge_files, key=lambda mf: mf.target_path)


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


def prune_overlapping_targets(merge, prefer_nonsource=False):
    """Removes merge files with overlapping target paths.

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
    source_lookup = {mf.target_path for mf in merge.files if mf.type == "s"}
    nonsource_lookup = {mf.target_path for mf in merge.files if mf.type != "s"}
    merge.files = [
        mf
        for mf in merge.files
        if _keep_for_prune_overlapping(
            mf,
            source_lookup,
            nonsource_lookup,
            prefer_nonsource,
        )
    ]


def _keep_for_prune_overlapping(mf, source_lookup, nonsource_lookup, prefer_nonsource):
    return not (
        mf.target_path in source_lookup and mf.target_path in nonsource_lookup
    ) or (mf.type != "s" if prefer_nonsource else mf.type == "s")
