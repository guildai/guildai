import hashlib
import logging
import os
import re

import guild.opref

from guild import pip_util
from guild import util
from guild import var

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

    def _link_to_source(self, source_path):
        link = self._link_path(source_path)
        util.ensure_dir(os.path.dirname(link))
        logging.debug("resolving source '%s' as link '%s'", source_path, link)
        os.symlink(source_path, link)

    def _link_path(self, source_path):
        basename = os.path.basename(source_path)
        res_path = self.resdef.path or ""
        if os.path.isabs(res_path):
            raise DependencyError(
                "invalid path '%s' in resource '%s' (path must be relative)"
                % (res_path, self.resdef.name))
        return os.path.join(self.ctx.target_dir, res_path, basename)

    def resolve(self):
        logging.info("Resolving '%s' resource", self.resdef.name)
        for source in self.resdef.sources:
            scheme = source.parsed_uri.scheme
            if scheme == "file":
                self._resolve_file_source(source)
            elif scheme in ["http", "https"]:
                self._resolve_url_source(source)
            elif scheme == "operation":
                self._resolve_operation_source(source)
            else:
                raise DependencyError(
                    "unsupported scheme in URL '%s' in resource '%s'"
                    % (source.uri, self.resdef.name))

    def _resolve_file_source(self, source):
        working_dir = os.path.dirname(self.resdef.modelfile.src)
        source_path = os.path.join(working_dir, source.parsed_uri.path)
        if not os.path.exists(source_path):
            raise DependencyError(
                "required file '%s' does not exist (file source "
                "in resource '%s')" % (source_path, self.resdef.name))
        _verify_file(source_path, source.sha256, self.ctx)
        self._link_to_source(source_path)

    def _resolve_url_source(self, source):
        source_path = _ensure_url_source(source)
        self._link_to_source(source_path)

    def _resolve_operation_source(self, source):
        opref, path = self._parse_opref(source.parsed_uri.path)
        run = self._latest_op_run(opref)
        source_path = os.path.join(run.path, path)
        if not os.path.exists(source_path):
            raise DependencyError(
                "required output '%s' (operation source in resource '%s') "
                "was not generated in the latest run (%s)"
                % (path, self.resdef.name, run.id))
        self._link_to_source(source_path)

    def _parse_opref(self, opref_spec):
        try:
            opref, path = guild.opref.OpRef.from_string(opref_spec)
        except guild.opref.OpRefError:
            raise DependencyError(
                "inavlid operation reference '%s' in resource '%s'"
                % (opref_spec, self.resdef.name))
        else:
            if not path or path[0] != '/':
                raise DependencyError(
                    "invalid operation source path '%s' in resource '%s'"
                    % (path, self.resdef.name))
            normalized_path = os.path.join(*path.split("/"))
            return opref, normalized_path

    def _latest_op_run(self, opref):
        resolved_opref = self._fully_resolve_opref(opref)
        completed_op_runs = var.run_filter("all", [
            var.run_filter("any", [
                var.run_filter("attr", "extended_status", "completed"),
                var.run_filter("attr", "extended_status", "running"),
            ]),
            resolved_opref.is_op_run])
        runs = var.runs(sort=["-started"], filter=completed_op_runs)
        if runs:
            return runs[0]
        raise DependencyError(
            "completed run for %s does not exist (operation source "
            "in resource '%s')"
            % (self._opref_desc(resolved_opref), self.resdef.name))

    @staticmethod
    def _opref_desc(opref):
        pkg = "." if opref.pkg_type == "modelfile"  else opref.pkg_name
        return "%s/%s:%s" % (pkg, opref.model_name, opref.op_name)

    def _fully_resolve_opref(self, opref):
        assert opref.op_name, opref
        package_version = None
        return guild.opref.OpRef(
            opref.pkg_type or "modelfile",
            opref.pkg_name or os.path.abspath(self.resdef.modelfile.src),
            package_version,
            opref.model_name or self.resdef.modeldef.name,
            opref.op_name)

def _verify_file(path, sha256, ctx):
    _verify_file_exists(path, ctx)
    if sha256:
        _verify_file_hash(path, sha256)

def _verify_file_exists(path, ctx):
    if not os.path.exists(path):
        raise DependencyError(
            "'%s' required by operation '%s' does not exist"
            % (path, ctx.opdef.fullname))

def _verify_file_hash(path, sha256):
    actual = util.file_sha256(path)
    if actual != sha256:
        raise DependencyError(
            "unexpected sha256 for '%s' (expected %s but got %s)"
            % (path, sha256, actual))

def _ensure_url_source(source):
    download_dir = _download_dir_for_url(source.parsed_uri)
    util.ensure_dir(download_dir)
    try:
        return pip_util.download_url(source.uri, download_dir, source.sha256)
    except pip_util.HashMismatch as e:
        raise DependencyError(
            "bad sha256 for '%s' (expected %s but got %s)"
            % (source.url, e.expected, e.actual))

def _download_dir_for_url(parsed_url):
    key = "\n".join(parsed_url).encode("utf-8")
    digest = hashlib.sha224(key).hexdigest()
    return os.path.join(var.cache_dir("resources"), digest)

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
            % (spec, ctx.opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, ctx)

def _packaged_resource(_spec, _ctx):
    # TODO
    return None
