import errno
import logging
import os

import yaml

import guild.plugin

class ProjectError(Exception):

    def __init__(self, path):
        super(ProjectError, self).__init__(path)
        self.path = path

class ProjectFormatError(ProjectError):
    pass

class NoModels(ProjectError):
    pass

class Project(object):

    def __init__(self, data, src):
        self._data = data
        self.src = src
        self.models = [
            Model(self, model_data) for model_data in data
        ]

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

    def default_model(self):
        return self.models[0] if self.models else None

class Model(object):

    def __init__(self, project, data):
        self.project = project
        self._data = data
        self.name = data.get("name")
        self.version = data.get("version")
        self.description = data.get("description")
        self.operations = _sorted_ops(data.get("operations", {}), self)
        self.flags = data.get("flags", {})
        self.disabled_plugins = data.get("disabled-plugins", [])

    def get_op(self, name):
        for op in self.operations:
            if op.name == name:
                return op
        return None

    def __repr__(self):
        return "<guild.project.Model '%s'>" % self.name

def _sorted_ops(data, model):
    keys = sorted(data.keys())
    return [Operation(model, key, data[key]) for key in keys]

class Operation(object):

    def __init__(self, model, name, data):
        self.model = model
        self.project = model.project
        self.name = name
        data = _coerce_op_data(data)
        self._data = data
        self.description = data.get("description")
        self.cmd = data.get("cmd")
        self.flags = data.get("flags", {})
        self.disabled_plugins = data.get("disabled-plugins", [])

    @property
    def full_name(self):
        return "%s:%s" % (self.model.name, self.name)

    def __repr__(self):
        return "<guild.project.Operation '%s'>" % self.full_name

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

def from_dir(path, filenames=["MODELS", "MODEL"], use_plugins=True):
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
            return Project(_load_modelfile(model_file), model_file)
    return None

def _try_from_plugin(path):
    data = []
    for name, plugin in guild.plugin.iter_plugins():
        logging.debug(
            "checking '%s' for models with plugin '%s'",
            path, name)
        plugin_models = _plugin_models_for_location(plugin, path)
        for model in plugin_models:
            logging.debug(
                "found model '%s' with plugin '%s'",
                model.get("name"), name)
        data.extend(plugin_models)
    if data:
        return Project(data, os.path.join(path, "__generated__"))
    else:
        return None

def _raise_no_models(path):
    raise NoModels(path)

def from_file(src):
    return Project(_load_modelfile(src), src)

def _load_modelfile(path):
    with open(path, "r") as f:
        data = yaml.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ProjectFormatError(path)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise
