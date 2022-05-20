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

import fnmatch
import os

from guild import file_util
from guild import run_manifest


class MergeError(Exception):
    pass


class MergeFile:
    def __init__(self, type, run_path, project_path):
        self.type = type
        self.run_path = run_path
        self.project_path = project_path

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} type='{self.type}' "
            f"run_path='{self.run_path}' project_path='{self.project_path}'>"
        )


class RunMerge:
    def __init__(
        self,
        run,
        dest=None,
        skip_sourcecode=False,
        skip_deps=False,
        skip_generated=False,
        exclude=None,
    ):
        self.run = run
        self.skip_sourcecode = skip_sourcecode
        self.skip_deps = skip_deps
        self.skip_generated = skip_generated
        self.exclude = exclude
        self.files = _init_merge_files(self)
        self.dest = dest or _run_guildfile_project_dir(run)


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
        raise MergeError(f"run manifest does not exist for {run.id}")
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
    run_path, _hash_arg, project_path = args[1:]
    index[run_path] = MergeFile("s", run_path, project_path)


def _apply_dep_entry_to_index(args, index):
    if not _is_project_local_dep_entry(args):
        return
    run_path, _hash_arg, project_path = args[1:]
    index[run_path] = MergeFile("d", run_path, project_path)


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
        or _path_excluded(merge_file.project_path, merge.exclude)
    )


def _path_excluded(path, exclude_patterns):
    if not exclude_patterns:
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in exclude_patterns)


def _run_guildfile_project_dir(run):
    if not run.opref.pkg_type == "guildfile":
        raise MergeError(
            f"cannot determine project directory for run {run.id} - run not "
            f"generated from a Guild file (package type '{run.opref.pkg_type}')"
        )
    project_dir = os.path.dirname(run.opref.pkg_name)
    if not os.path.exists(project_dir):
        raise MergeError(
            "project directory '{project_dir}' for run {run.id} does not exist"
        )
    return project_dir
