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

from __future__ import absolute_import
from __future__ import division

import errno
import logging
import os

import yaml

import guild.plugin
import guild.util

# The order here should be based on priority of selection.
NAMES = ["MODELS", "MODEL"]

class ModelfileError(Exception):

    def __init__(self, path):
        super(ModelfileError, self).__init__(path)
        self.path = path

class ModelfileFormatError(ModelfileError):
    pass

class NoModels(ModelfileError):
    pass

class Modelfile(object):

    def __init__(self, data, src):
        self._data = data
        self.src = src
        self.models = [
            ModelDef(self, model_data) for model_data in data
        ]

    def __repr__(self):
        return "<guild.modelfile.Modelfile '%s'>" % self.src

    def __iter__(self):
        return iter(self.models)

    def get(self, model_name, default=None):
        for model in self.models:
            if model.name == model_name:
                return model
        return default

    def __getitem__(self, model_name):
        model = self.get(model_name)
        if model is None:
            raise KeyError(model_name)
        return model

    @property
    def default_model(self):
        return self.models[0] if self.models else None

class FlagValHost(object):

    def __init__(self, parent_host=None):
        self._parent = parent_host
        self._flag_vals = {}

    def all_flag_values(self):
        seen = set()
        for name in self._flag_vals:
            yield name, self._flag_vals[name]
            seen.add(name)
        if self._parent:
            # pylint: disable=protected-access
            for name in self._parent._flag_vals:
                if name not in seen:
                    yield name, self._parent._flag_vals[name]
                    seen.add(name)

    def set_flag_value(self, name, val):
        self._flag_vals[name] = val

    def get_flag_value(self, name, default=None):
        try:
            return self._flag_vals[name]
        except KeyError:
            return (self._parent.get_flag_val(name)
                    if self._parent
                    else default)

class ModelDef(FlagValHost):

    def __init__(self, modelfile, data):
        super(ModelDef, self).__init__()
        self.modelfile = modelfile
        self._data = data
        self.name = data.get("name")
        self.description = data.get("description")
        self.operations = _sorted_ops(data.get("operations", {}), self)
        self.flags = _sorted_flags(data.get("flags", {}), self)
        for flag in self.flags:
            self.set_flag_value(flag.name, flag.value)
        self.disabled_plugins = data.get("disabled-plugins", [])

    def __repr__(self):
        return "<guild.modelfile.Model '%s'>" % self.name

    def get_op(self, name):
        for op in self.operations:
            if op.name == name:
                return op
        return None

def _sorted_flags(data, parent):
    keys = sorted(data.keys())
    return [FlagDef(parent, key, data[key]) for key in keys]

class FlagDef(object):

    def __init__(self, parent, name, data):
        self.parent = parent
        self.name = name
        self.description = data.get("description")
        self.value = data.get("value")

    def __repr__(self):
        return "<guild.modelfile.Flag '%s'>" % self.name

def _sorted_ops(data, model):
    keys = sorted(data.keys())
    return [OpDef(model, key, data[key]) for key in keys]

class OpDef(FlagValHost):

    def __init__(self, modeldef, name, data):
        super(OpDef, self).__init__(modeldef)
        self.modeldef = modeldef
        self.modelfile = modeldef.modelfile
        self.name = name
        data = _coerce_op_data(data)
        self._data = data
        self.description = data.get("description")
        self.cmd = data.get("cmd")
        self.flags = _sorted_flags(data.get("flags", {}), self)
        for flag in self.flags:
            self.set_flag_value(flag.name, flag.value)
        self.disabled_plugins = data.get("disabled-plugins", [])

    def __repr__(self):
        return "<guild.modelfile.Operation '%s'>" % self.fullname

    @property
    def fullname(self):
        return "%s:%s" % (self.modeldef.name, self.name)

def _coerce_op_data(data):
    """Return a cmd map for data.

    Ops may be strings, in which case the value is implied as the cmd
    attribute of the op map.
    """
    if isinstance(data, str):
        return {
            "cmd": data
        }
    else:
        return data

def from_dir(path, filenames=None, use_plugins=True):
    filenames = NAMES if filenames is None else filenames
    return guild.util.find_apply([
        lambda: _try_from_dir_file(path, filenames),
        lambda: _try_from_plugin(path) if use_plugins else None,
        lambda: _raise_no_models(path)])

def _try_from_dir_file(path, filenames):
    logging.debug("checking '%s' for model sources", path)
    for name in filenames:
        model_file = os.path.abspath(os.path.join(path, name))
        if os.path.isfile(model_file):
            logging.debug("found model source '%s'", model_file)
            return Modelfile(_load_modelfile(model_file), model_file)
    return None

def _try_from_plugin(path):
    data = []
    for name, plugin in guild.plugin.iter_plugins():
        logging.debug(
            "using plugin '%s' to check '%s' for models",
            name, path)
        plugin_models = _plugin_models_for_location(plugin, path)
        for model in plugin_models:
            logging.debug(
                "found model '%s' with plugin '%s'",
                model.get("name"), name)
        data.extend(plugin_models)
    if data:
        return Modelfile(data, os.path.join(path, "__generated__"))
    else:
        return None

def _plugin_models_for_location(plugin, path):
    return list(plugin.models_for_location(path) or [])

def _raise_no_models(path):
    raise NoModels(path)

def from_file(src):
    return Modelfile(_load_modelfile(src), src)

def _load_modelfile(path):
    data = yaml.load(open(path, "r"))
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        raise ModelfileFormatError(path)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise
