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

from guild import filter as filterlib
from guild import index as indexlib
from guild import var


class _FilterRun:
    def __init__(self, run, index):
        self._run = run
        self._index = index
        self._scalars = None

    def get_attr(self, name):
        return self._index.run_attr(self._run, name)

    def get_flag(self, name):
        return self._index.run_flag(self._run, name)

    def get_scalar(self, key):
        return _find_scalar(key, self._ensure_scalars())

    def _ensure_scalars(self):
        if self._scalars is None:
            self._scalars = list(self._index.run_scalars(self._run))
        return self._scalars


def _find_scalar(key, scalars):
    prefix, tag = _split_scalar_key(key)
    for entry in scalars:
        if (not prefix or prefix == entry["prefix"]) and tag == entry["tag"]:
            return entry
    return None


def _split_scalar_key(key):
    parts = key.split("#", 1)
    if len(parts) == 2:
        return parts
    return None, parts[0]


def filtered_runs(
    filter,
    root=None,
    sort=None,
    base_filter=None,
    force_root=False,
    index=None,
):
    if isinstance(filter, str):
        filter = filterlib.parser().parse(filter)
    runs = var.runs(root=root, sort=sort, filter=base_filter, force_root=force_root)
    index = index or indexlib.RunIndex()
    index.refresh(runs, _index_refresh_types(filter))
    return [run for run in runs if _filter_run(filter, run, index)]


def _index_refresh_types(filter):
    """Refresh types are provided by an optional `index_refresh_types` attribute."""
    return getattr(filter, "index_refresh_types", None)


def _filter_run(f, run, index):
    return f(_FilterRun(run, index))
