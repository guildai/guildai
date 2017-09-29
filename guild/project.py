import errno
import os

import yaml

class ProjectError(Exception):

    def __init__(self, path):
        super(ProjectError, self).__init__(path)
        self.path = path

class ProjectFormatError(ProjectError):
    pass

class MissingSourceError(ProjectError):
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
        self.name = name
        data = _coerce_op_data(data)
        self._data = data
        self.cmd = data.get("cmd")

    def __repr__(self):
        return ("<guild.project.Operation '%s:%s'>"
                % (self.model.name, self.name))

def _coerce_op_data(data):
    if isinstance(data, str):
        return {
            "cmd": data
        }
    else:
        return data

def from_dir(path, filenames=["MODELS", "MODEL"]):
    for name in filenames:
        modelfile = os.path.abspath(os.path.join(path, name))
        if os.path.isfile(modelfile):
            return Project(_load_modelfile(modelfile), modelfile)
    raise MissingSourceError(path)

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
