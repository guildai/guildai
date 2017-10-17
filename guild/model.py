from . import entry_point_util

class Model(object):
    name = None

def _init_model(model, ep):
    print("*********", model, ep)

_models = entry_point_util.EntryPointResources(
    "guild.models", "model", _init_model)

iter_models = _models.__iter__
