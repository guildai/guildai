import os

import yaml

class ProjectError(Exception):

    def __init__(self, path):
        super(ProjectError, self).__init__(path)
        self.path = path
    
class ProjectFormatError(ProjectError):
    pass

class NoSourcesError(ProjectError):
    pass

class Project(object):

    def __init__(self, data, srcs):
        self._data = data
        self.srcs = srcs
        self.models = [
            Model(model_data) for model_data in data
        ]

    def __iter__(self):
        return iter(self.models)

class Model(object):

    def __init__(self, data):
        self._data = data
        self.name = data.get("name")
        self.operations = [
            Operation(op_data) for op_data in data.get("operations", [])
        ]

class Operation(object):

    def __init__(self, data):
        data = _coerce_op_data(data)
        self._data = data
        self.cmd = data.get("cmd")

def _coerce_op_data(data):
    if isinstance(data, str):
        return {
            "cmd": data
        }
    else:
        return data

def from_dir(path, filenames=["MODEL", "MODELS"]):
    data = []
    srcs = []
    for filename in filenames:
        modelfile = os.path.join(path, filename)
        if os.path.isfile(modelfile): 
            data.extend(_load_modelfile(modelfile))
            srcs.append(modelfile)
    if not srcs:
        raise NoSourcesError(path)
    return Project(data, srcs)

def from_file(src):
    return Project(_load_modelfile(src), [src])

def _load_modelfile(path):
    with open(path, "r") as f:
        data = yaml.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ProjectFormatError(path)
