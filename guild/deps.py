import logging
import os
import re

from guild import modelfile
from guild import util

RESOURCE_TERM = r"[a-zA-Z0-9_\-\.]+"

class DependencyError(Exception):
    pass

class ResolutionContext(object):

    def __init__(self, target_dir, opdef):
        self.target_dir = target_dir
        self.opdef = opdef

class Resource(object):

    def __init__(self, resdef, ctx):
        self.resdef = resdef
        self.ctx = ctx

    def resolve(self):
        for source in self.resdef.sources:
            if isinstance(source, modelfile.FileSource):
                self._resolve_file_source(source)
            elif isinstance(source, modelfile.URLSource):
                self._resolve_url_source(source)
            else:
                raise AssertionError(source)

    def _resolve_file_source(self, source):
        working_dir = os.path.dirname(self.resdef.modelfile.src)
        source_path = os.path.join(working_dir, source.path)
        _verify_file(source_path, source.sha256, self.ctx)
        target_path = os.path.join(
            self.ctx.target_dir,
            os.path.basename(source.path))
        util.ensure_dir(os.path.dirname(target_path))
        logging.debug(
            "resolving source '%s' as link '%s'",
            source_path, target_path)
        os.symlink(source_path, target_path)

    def _resolve_url_source(self, source):
        print("TODO: resolve %s" % source)

def _verify_file(path, sha256, ctx):
    _verify_file_exists(path, ctx)
    if sha256:
        _verify_file_hash(path, sha256)

def _verify_file_exists(path, ctx):
    if not os.path.exists(path):
        raise DependencyError(
            "'%s' required by operation '%s' does not exist"
            % (path, ctx.opdef.fullname))

def _verify_file_hash(path, expected_sha256):
    actual = util.file_sha256(path)
    if actual != expected_sha256:
        raise DependencyError(
            "unexpected sha256 hash for '%s' (expected %s but got %s)"
            % (path, expected_sha256, actual))

def _dep_desc(dep):
    return "%s:%s" % (dep.opdef.modeldef.name, dep.opdef.name)

def resolve(dependencies, ctx):
    for dep in dependencies:
        resource = _dependency_resource(dep.spec, ctx)
        resource.resolve()

def _dependency_resource(spec, ctx):
    res = util.find_apply(
        [_model_resource,
         _modelfile_resource,
         _packaged_resource],
        spec, ctx)
    if res:
        return res
    raise DependencyError(
        "invalid dependency '%s' in operation '%s'"
        % (spec, ctx.opdef.fullname))

def _model_resource(spec, ctx):
    m = re.match(r"(%s)$" % RESOURCE_TERM, spec)
    if m is None:
        return None
    res_name = m.group(1)
    return _modeldef_resource(ctx.opdef.modeldef, res_name, ctx)

def _modeldef_resource(modeldef, res_name, ctx):
    resdef = modeldef.get_resource(res_name)
    if resdef is None:
        raise DependencyError(
            "resource '%s' required by operation '%s' is not defined"
            % (res_name, ctx.opdef.fullname))
    return Resource(resdef, ctx)

def _modelfile_resource(spec, ctx):
    m = re.match(r"(%s):(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = ctx.opdef.modelfile.get(model_name)
    if modeldef is None:
        raise DependencyError(
            "model in resource '%s' required by operation "
            "'%s' is not defined"
            % (model_name, spec, ctx.opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, ctx)

def _packaged_resource(spec, ctx):
    return None
