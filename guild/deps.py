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

import logging
import os
import re

from guild import namespace
from guild import resource
from guild import util
from guild.resolve import ResolutionError

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
        if os.path.exists(link):
            logging.warning("source '%s' already exists, skipping link", link)
            return
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
            self._resolve_source(source)

    def _resolve_source(self, source):
        resolver = self.resdef.get_source_resolver(source)
        if not resolver:
            raise DependencyError(
                "unsupported source '%s' in resource '%s'"
                % (source, self.resdef.name))
        try:
            source_path = resolver.resolve()
        except ResolutionError as e:
            raise DependencyError(
                "could not resolve '%s' in '%s' resource: %s"
                % (source, self.resdef.name, e))
        else:
            self._verify_file(source_path, source.sha256)
            self._link_to_source(source_path)

    def _verify_file(self, path, sha256):
        self._verify_file_exists(path)
        if sha256:
            self._verify_file_hash(path, sha256)

    def _verify_file_exists(self, path):
        if not os.path.exists(path):
            raise DependencyError(
                "'%s' required by operation '%s' does not exist"
                % (path, self.ctx.opdef.fullname))

    def _verify_file_hash(self, path, sha256):
        actual = util.file_sha256(path)
        if actual != sha256:
            raise DependencyError(
                "'%s' required by operation '%s' has an unexpected sha256 "
                "(expected %s but got %s)"
                % (path, self.ctx.opdef.fullname, sha256, actual))

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

def _packaged_resource(spec, ctx):
    m = re.match(r"(%s)/(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    for res in resource.for_name(res_name):
        if namespace.apply_namespace(res.dist.project_name) == pkg_name:
            return Resource(res.resdef, ctx)
    return None
