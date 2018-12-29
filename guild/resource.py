# Copyright 2017-2019 TensorHub, Inc.
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

from guild import entry_point_util
from guild import namespace

_resources = entry_point_util.EntryPointResources("guild.resources", "resource")

class Resource(object):

    def __init__(self, ep):
        self.name = ep.name
        self.dist = ep.dist
        self.resdef = self._init_resdef()
        self._fullname = None # lazy

    def __repr__(self):
        return "<guild.resource.Resource '%s'>" % self.fullname

    @property
    def fullname(self):
        if self._fullname is None:
            package_name = namespace.apply_namespace(self.dist.project_name)
            self._fullname = "%s/%s" % (package_name, self.name)
        return self._fullname

    def _init_resdef(self):
        raise NotImplementedError()

def set_path(path):
    _resources.set_path(path)

def insert_path(item):
    path = _resources.path()
    try:
        path.remove(item)
    except ValueError:
        pass
    path.insert(0, item)
    _resources.set_path(path)

def iter_resources():
    for _name, res in _resources:
        if not res.resdef.private:
            yield res

def for_name(name):
    return _resources.for_name(name)
