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
from guild import run_util


class MergeError(Exception):
    pass


class MergeFile:
    def __init__(self, run, rel_path, dest):
        self.run = run
        self.rel_path = rel_path
        self.src = os.path.join(run.dir, rel_path)
        self.dest = dest


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
        self.files = _init_merge_files(
            run,
            skip_sourcecode,
            skip_deps,
            skip_generated,
            exclude,
        )
        self.dest = dest or _run_guildfile_project_dir(run)


def _init_merge_files(run, skip_sourcecode, skip_deps, skip_generated, exclude):
    files = []
    if not skip_sourcecode:
        files.extend(_sourcecode_files(run))
    if not skip_deps:
        files.extend(_project_local_deps(run))
    if not skip_generated:
        files.extend(_generated_files(run))
    return _filter_excluded(files, exclude)


def _sourcecode_files(run):
    return file_util.find(
        run_util.sourcecode_dir(run),
        followlinks=True,
        includedirs=True,
        unsorted=True,
    )


def _project_local_deps(run):
    # TODO
    return []


def _generated_files(run):
    # TODO
    return []


def _filter_excluded(files, exclude):
    exclude = exclude or []
    return [path for path in files if not _excluded(path, exclude)]


def _excluded(path, exclude_patterns):
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
