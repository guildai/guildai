from . import namespace

def model_fullname(model):
    pkg_name = namespace.apply_namespace(model.dist.project_name)
    return "%s/%s" % (pkg_name, model.name)

def op_fullname(model, op):
    return "%s:%s" % (model_fullname(model), op.opdef.name)
