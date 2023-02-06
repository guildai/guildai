# Copyright 2017-2023 Posit Software, PBC
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

import os
import re

from guild import run as runlib


def init_step_run(parent_run_dir):
    """Initialize the run dir for a step run.

    Directory is based on a new, unique run ID but is not created.

    Returns a step run.
    """
    runs_dir = os.path.dirname(parent_run_dir)
    step_run_id = runlib.mkid()
    step_run_dir = os.path.join(runs_dir, step_run_id)
    return runlib.Run(step_run_id, step_run_dir)


def link_to_step_run(step_name, step_run_dir, parent_run_dir):
    """Create a link to a step run in a parent run dir.

    Uses `step_name` for the link name. If a file with that name
    already exists in the parent run dir, appends a suffix '_N' where
    `N` is the next available unique integer starting with `2`.

    Returns the full path to the created link.
    """
    link_name = _step_link_name(step_name)
    link_path_base = os.path.join(parent_run_dir, link_name)
    link_path = _ensure_unique_link(link_path_base)
    rel_step_run_dir = os.path.relpath(step_run_dir, os.path.dirname(link_path))
    os.symlink(rel_step_run_dir, link_path)
    return link_path


def _step_link_name(step_name):
    return re.sub(r"[ :/\\]", "-", str(step_name))


def _ensure_unique_link(path_base):
    v = 2
    path = path_base
    while True:
        _infinite_loop_check(v)
        if not os.path.lexists(path):
            return path
        path = f"{path_base}_{v}"
        v += 1


def _infinite_loop_check(v):
    assert v < 1e8
