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

from guild import resourcedef
from guild import util

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

class ModelfileReferenceError(ModelfileError):
    pass

class Modelfile(object):

    def __init__(self, data, src):
        self.data = data
        self.src = src
        self.models = [
            ModelDef(self, model_data) for model_data in data
        ]

    def __repr__(self):
        return "<guild.modelfile.Modelfile '%s'>" % self.src

    def __str__(self):
        return self.src

    def __iter__(self):
        return iter(self.models)

    def __eq__(self, x):
        if isinstance(x, Modelfile):
            return os.path.abspath(self.src) == os.path.abspath(x.src)
        return False

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

class FlagHost(object):

    def __init__(self, host_data, modelfile, parent_host=None):
        self.flags = _init_flags(host_data, modelfile)
        self._parent = parent_host
        self._flag_vals = _init_flag_values(self.flags)

    def get_flagdef(self, name):
        for flag in self.flags:
            if flag.name == name:
                return flag
        return None

    def flag_values(self):
        return dict(self._iter_flag_values())

    def _iter_flag_values(self):
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

def _init_flags(host_data, modelfile):
    flags = {}
    seen_includes = set()
    if isinstance(host_data, dict):
        flags_data = host_data.get("flags", {})
        if isinstance(flags_data, str):
            _apply_flag_includes(flags_data.split(), modelfile, seen_includes, flags)
        elif isinstance(flags_data, dict):
            _apply_flag_data(flags_data, modelfile, seen_includes, flags)
        else:
            raise ModelfileFormatError("invalid flag data: %s" % flags_data)
    return [flags[name] for name in sorted(flags)]

def _apply_flag_includes(includes, modelfile, seen_includes, flags):
    # This init scheme is a bit fiddly. We're accessing modelfile.data
    # here rather than use the modefile interface because the modefile
    # is still being initialized. By accessing the underlying data we
    # can resolve includes without resorting to a two-pass flag init
    # process (i.e. load include refs in one pass and resolve them in
    # a second pass).
    assert hasattr(modelfile, "data"), "refer to source code comment"
    for ref in includes:
        if ref in seen_includes:
            break
        seen_includes.add(ref)
        for model in modelfile.data:
            if model.get("name") == ref:
                flag_data = model.get("flags", {})
                _apply_flag_data(flag_data, modelfile, seen_includes, flags)
                break
        else:
            raise ModelfileReferenceError(
                "model '%s' for flag include doesn't exist" % ref)

def _apply_flag_data(data, modelfile, seen_includes, flags):
    # Apply includes before other defs to support redefining included
    # values.
    for name in _includes_first(data):
        if name == "$include":
            _apply_flag_includes(data[name].split(), modelfile, seen_includes, flags)
        else:
            _apply_flag(FlagDef(name, data[name]), flags)

def _includes_first(names):
    return sorted(names, key=lambda x: "\x00" if x == "$include" else x)

def _apply_flag(flag, flags):
    try:
        cur = flags[flag.name]
    except KeyError:
        flags[flag.name] = flag
    else:
        if flag.value is not None:
            cur.value = flag.value
        if flag.description is not None:
            cur.description = flag.description

def _init_flag_values(flagdefs):
    return {
        flag.name: flag.value
        for flag in flagdefs
    }

class FlagDef(object):

    def __init__(self, name, data):
        self.name = name
        if isinstance(data, dict):
            self.value = data.get("value")
            self.description = data.get("description")
        elif isinstance(data, (str, int, float, bool)):
            self.value = data
            self.description = None
        else:
            raise ModelfileFormatError("unsupported flag data: %s" % data)

class Visibility(object):

    public = "public"
    private = "private"

class ModelDef(FlagHost):

    def __init__(self, modelfile, data):
        super(ModelDef, self).__init__(data, modelfile)
        self.modelfile = modelfile
        self._data = data
        self.name = data.get("name")
        self.description = data.get("description", "").strip()
        self.visibility = data.get("visibility", Visibility.public)
        self.operations = _init_ops(data.get("operations", {}), self)
        self.resources = resourcedef.from_data(data.get("resources"), self.modelfile)
        self.disabled_plugins = data.get("disabled-plugins", [])

    def __repr__(self):
        return "<guild.modelfile.ModelDef '%s'>" % self.name

    def get_op(self, name):
        for op in self.operations:
            if op.name == name:
                return op
        return None

def _init_ops(data, modeldef):
    keys = sorted(data.keys())
    return [OpDef(modeldef, key, data[key]) for key in keys]

class OpDef(FlagHost):

    def __init__(self, modeldef, name, data):
        super(OpDef, self).__init__(data, modeldef.modelfile, modeldef)
        self.modeldef = modeldef
        self.modelfile = modeldef.modelfile
        self.name = name
        data = _coerce_op_data(data)
        self._data = data
        self.description = data.get("description")
        self.cmd = data.get("cmd")
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.requires = _coerce_string_list(data.get("requires"))

    def __repr__(self):
        return "<guild.modelfile.OpDef '%s'>" % self.fullname

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

def _coerce_string_list(data):
    if isinstance(data, list):
        return [str(x) for x in data]
    else:
        return [str(data)]

def from_dir(path, filenames=None, use_plugins=True):
    filenames = NAMES if filenames is None else filenames
    return util.find_apply([
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
