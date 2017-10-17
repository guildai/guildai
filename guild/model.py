from . import entry_point_util

class Model(object):

    name = None
    dist = None

def _init_model(model, ep):
    model.name = ep.name
    model.dist = ep.dist

_models = entry_point_util.EntryPointResources(
    "guild.models", "model", _init_model)

iter_models = _models.__iter__
for_name = _models.for_name
limit_to_paths = _models.limit_to_paths
