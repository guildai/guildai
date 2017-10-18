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

import logging
import os
import sys

from pkg_resources import Distribution, EntryPoint, register_finder

from .entry_point_util import EntryPointResources
from . import project as modelfile

_models = EntryPointResources("guild.models", "model")

class Model(object):

    def __init__(self, ep):
        self.name = ep.name
        self.dist = ep.dist

class ModelfileDistribution(Distribution):

    def __init__(self, models):
        super(ModelfileDistribution, self).__init__(
            location=os.path.dirname(models.src))
        self._entry_map = _entry_map_for_models(models, self)

    def get_entry_map(self, group=None):
        if group is None:
            return self._entry_map
        else:
            return self._entry_map.get(group, {})

def _entry_map_for_models(models, dist):
    return {
        "guild.models": {
            model.name: _entry_point_for_model(model, dist)
            for model in models
        }
    }

def _entry_point_for_model(model, dist):
    return EntryPoint(
        name=model.name,
        module_name=__name__,
        attrs=(Model.__name__,),
        dist=dist)

class ModelImportError(ImportError):
    pass

class ModelImporter(object):

    def __init__(self, path):
        if (not os.path.isfile(path) or
            os.path.basename(path) not in modelfile.NAMES):
            raise ModelImportError(path)

    @staticmethod
    def find_module(_fullname, _path=None):
        return None

def _model_finder(_importer, path, _only=False):
    try:
        models = modelfile.from_file(path)
    except (IOError, modelfile.ModelFormatError) as e:
        logging.warning(
            "unable to load model file '%s': %s",
            path, e)
    else:
        yield ModelfileDistribution(models)

def iter_models():
    return iter(_models)

def for_name(name):
    return _models.for_name(name)

def path():
    return _models.path()

def set_path(path):
    _models.set_path(path)

def add_model_source(filename):
    path = _models.path()
    try:
        path.remove(filename)
    except ValueError:
        pass
    path.insert(0, filename)
    _models.set_path(path)

def _register_model_finder():
    sys.path_hooks.insert(0, ModelImporter)
    register_finder(ModelImporter, _model_finder)

_register_model_finder()
