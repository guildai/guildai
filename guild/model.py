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

import base64
import hashlib
import logging
import os
import sys

import pkg_resources

from . import entry_point_util
from . import modelfile

_models = entry_point_util.EntryPointResources("guild.models", "model")

class Model(object):

    def __init__(self, ep):
        self.name = ep.name
        self.dist = ep.dist
        self.modeldef = _modeldef_for_dist(ep.name, ep.dist)

    def __repr__(self):
        return "<guild.model.Model '%s'>" % self.name

    @property
    def reference(self):
        try:
            modelfile = self.dist.modelfile
        except AttributeError:
            return "dist:%s %s" % (self.dist, self.name)
        else:
            return "file:%s %s" % (_modelfile_dist_ref(modelfile), self.name)

def _modeldef_for_dist(name, dist):
    if isinstance(dist, ModelfileDistribution):
        return dist.get_model(name)
    else:
        for modeldef in _ensure_dist_modeldefs(dist):
            if modeldef.name == name:
                return modeldef
        raise ValueError("undefined model '%s'" % name)

def _ensure_dist_modeldefs(dist):
    # pylint: disable=protected-access
    if not hasattr(dist, "_modelefs"):
        dist._modeldefs = _load_dist_modeldefs(dist)
    return dist._modeldefs

def _load_dist_modeldefs(dist):
    modeldefs = []
    try:
        record = dist.get_metadata_lines("RECORD")
    except IOError:
        logging.warning(
            "distribution %s missing RECORD metadata - unable to find models",
            dist)
    else:
        for line in record:
            path = line.split(",", 1)[0]
            if os.path.basename(path) in modelfile.NAMES:
                fullpath = os.path.join(dist.location, path)
                _try_acc_modeldefs(fullpath, modeldefs)
    return modeldefs

def _try_acc_modeldefs(path, acc):
    try:
        models = modelfile.from_file(path)
    except Exception as e:
        logging.warning("unable to load models from %s: %s", path, e)
    else:
        for modeldef in models:
            acc.append(modeldef)

def _modelfile_dist_ref(modelfile):
    path = os.path.abspath(modelfile.src)
    return "%s %s" % (path, _modelfile_hash(path))

def _modelfile_hash(path):
    try:
        path_bytes = open(path, "rb").read()
    except IOError:
        logging.warning("unable to read %s to calculate modelfile hash", path)
        return "-"
    else:
        return hashlib.md5(path_bytes).hexdigest()

class ModelfileDistribution(pkg_resources.Distribution):

    def __init__(self, modelfile):
        super(ModelfileDistribution, self).__init__(
            modelfile.src, project_name=_modelfile_project_name(modelfile))
        self.modelfile = modelfile
        self._entry_map = _modelfile_entry_map(modelfile, self)

    def __repr__(self):
        return "<guild.model.ModelfileDistribution '%s'>" % self.modelfile.src

    def get_entry_map(self, group=None):
        if group is None:
            return self._entry_map
        else:
            return self._entry_map.get(group, {})

    def get_model(self, name):
        for model in self.modelfile:
            if model.name == name:
                return model
        raise ValueError(name)

def _modelfile_project_name(modelfile):
    """Returns a project name for a modelfile distribution.

    Modelfile distribution project names are of the format:

        '.modelfile.' + ESCAPED_MODELFILE_PATH

    ESCAPED_MODELFILE_PATH is a 'safe' project name (i.e. will not be
    modified in a call to `pkg_resources.safe_name`) that, when
    unescaped using `unescape_project_name`, is the relative path of
    the directory containing the modelfile. The modefile name itself
    (e.g. 'MODEL' or 'MODELS') is not contained in the path.

    Modelfile paths are relative to the current working directory
    (i.e. the value of os.getcwd() at the time they are generated) and
    always start with '.'.
    """
    pkg_path = os.path.relpath(os.path.dirname(modelfile.src))
    if pkg_path[0] != ".":
        pkg_path = os.path.join(".", pkg_path)
    safe_path = escape_project_name(pkg_path)
    return ".modelfile.%s" % safe_path

def escape_project_name(name):
    """Escapes name for use as a valie pkg_resources project name."""
    return base64.b16encode(name.encode("utf-8")).decode("utf-8")

def unescape_project_name(escaped_name):
    """Unescapes names escaped with `escape_project_name`."""
    return base64.b16decode(escaped_name).decode("utf-8")

def _modelfile_entry_map(modelfile, dist):
    return {
        "guild.models": {
            model.name: _model_entry_point(model, dist)
            for model in modelfile
        }
    }

def _model_entry_point(model, dist):
    return pkg_resources.EntryPoint(
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
    except (IOError, modelfile.ModelfileFormatError) as e:
        logging.warning(
            "unable to load model file '%s': %s",
            path, e)
    else:
        yield ModelfileDistribution(models)

def iter_models():
    for _name, model in _models:
        yield model

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
    pkg_resources.register_finder(ModelImporter, _model_finder)

_register_model_finder()
