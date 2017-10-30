# Copyright 2017 TensorHub, Inc.
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
from guild.model import ModelfileDistribution
from guild import namespace

_resources = entry_point_util.EntryPointResources("guild.resources", "resource")

class Resource(object):

    def __init__(self, ep):
        self.name = ep.name
        self.dist = ep.dist
        self.resdef = _resdef_for_dist(ep.name, ep.dist)
        self._fullname = None # lazy

    def __repr__(self):
        return "<guild.resource.Resource '%s'>" % self.name

    @property
    def fullname(self):
        if self._fullname is None:
            package_name = namespace.apply_namespace(self.dist.project_name)
            self._fullname = "%s/%s" % (package_name, self.name)
        return self._fullname

def _resdef_for_dist(name, dist):
    if isinstance(dist, ModelfileDistribution):
        model_name, res_name = _split_modelfile_res_name(name)
        modeldef = dist.modelfile.get(model_name)
        assert modeldef, (name, dist)
        resdef = modeldef.get_resource(res_name)
        assert resdef, (name, dist)
        return resdef
    else:
        raise ValueError("unsupported resource distribution: %s" % dist)

def _split_modelfile_res_name(name):
    parts = name.split(":", 1)
    if len(parts) != 2:
        raise ValueError("invalid modelfile resource name: %s" % name)
    return parts

def set_path(path):
    _resources.set_path(path)

def add_model_path(model_path):
    path = _resources.path()
    try:
        path.remove(model_path)
    except ValueError:
        pass
    path.insert(0, model_path)
    _resources.set_path(path)

def iter_resources():
    for _name, res in _resources:
        if not res.resdef.modeldef.private:
            yield res
