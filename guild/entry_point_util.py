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
import sys

import pkg_resources

log = logging.getLogger("guild")


class Resource:
    def __init__(self, ep):
        self._ep = ep
        self._inst = None

    def inst(self):
        if self._inst is None:
            self._inst = self._ep.resolve()(self._ep)
        return self._inst

    def __str__(self):
        return f"'{self._ep}' in {self._ep.dist}"


class EntryPointResources:
    def __init__(self, group, desc="resource"):
        self._group = group
        self._desc = desc
        self.__working_set = None
        self.__resources = None

    @property
    def _resources(self):
        if self.__resources is None:
            self.__resources = self._init_resources()
        return self.__resources

    @property
    def _working_set(self):
        if self.__working_set is not None:
            return self.__working_set
        return pkg_resources.working_set

    def _init_resources(self):
        resources = {}
        for ep in self._working_set.iter_entry_points(self._group):
            res_list = resources.setdefault(ep.name, [])
            res_list.append(Resource(ep))
        return resources

    def __iter__(self):
        for name in self._resources:
            for res_inst in self.for_name(name):
                yield name, res_inst

    def one_for_name(self, name):
        try:
            return next(self.for_name(name))
        except StopIteration as e:
            raise LookupError(name) from e

    def for_name(self, name):
        try:
            name_resources = self._resources[name]
        except KeyError as e:
            raise LookupError(name) from e
        else:
            for res in name_resources:
                try:
                    inst = res.inst()
                except Exception as e:
                    if log.getEffectiveLevel() <= logging.DEBUG:
                        log.exception("error initializing %s", res)
                    else:
                        log.error("error initializing %s: %s", res, e)
                else:
                    yield inst

    def path(self):
        return self._working_set.entries

    def set_path(self, val, clear_cache=False):
        if clear_cache:
            self._clear_path_importer_cache(val)
        self.__working_set = pkg_resources.WorkingSet(val)
        self.__resources = None

    @staticmethod
    def _clear_path_importer_cache(paths):
        for path in paths:
            try:
                del sys.path_importer_cache[path]
            except KeyError:
                pass
