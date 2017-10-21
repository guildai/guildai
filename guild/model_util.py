from . import package

def model_fullname(model):
    pkg_name = package.apply_namespace(model.dist.project_name)
    return "%s/%s" % (pkg_name, model.name)

def op_fullname(model, op):
    return "%s:%s" % (model_fullname(model), op.opdef.name)
