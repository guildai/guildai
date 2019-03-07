# Copyright 2017-2019 TensorHub, Inc.
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
import shlex

from guild import namespace
from guild import resource
from guild import util
from guild.resolver import ResolutionError

log = logging.getLogger("guild")

RESOURCE_TERM = r"[a-zA-Z0-9_\-\.]+"

class DependencyError(Exception):
    pass

class ResolutionContext(object):

    def __init__(self, target_dir, opdef, resource_config):
        self.target_dir = target_dir
        self.opdef = opdef
        self.resource_config = resource_config

class Resource(object):

    def __init__(self, resdef, location, ctx):
        self.resdef = resdef
        self.location = location
        self.ctx = ctx
        self.config = self._init_resource_config()
        self.dependency = None

    def _init_resource_config(self):
        for name, config in self.ctx.resource_config.items():
            if name in [self.resdef.fullname, self.resdef.name]:
                return config
        return None

    def resolve(self, unpack_dir=None):
        resolved_acc = []
        for source in self.resdef.sources:
            paths = self.resolve_source(source, unpack_dir)
            resolved_acc.extend(paths)
        return resolved_acc

    def resolve_source(self, source, unpack_dir=None):
        resolver = self.resdef.get_source_resolver(source, self)
        if not resolver:
            raise DependencyError(
                "unsupported source '%s' in %s resource"
                % (source, self.resdef.name))
        try:
            source_paths = resolver.resolve(unpack_dir)
        except ResolutionError as e:
            msg = (
                "could not resolve '%s' in %s resource: %s"
                % (source, self.resdef.name, e))
            if source.help:
                msg += "\n%s" % source.help
            raise DependencyError(msg)
        except Exception as e:
            log.exception(
                "resolving required source '%s' in %s resource",
                source, self.resdef.name)
            raise DependencyError(
                "unexpected error resolving '%s' in %s resource: %r"
                % (source, self.resdef.name, e))
        else:
            paths = []
            for path in source_paths:
                paths.append(path)
                self._link_to_source(path, source)
            return paths

    def _link_to_source(self, source_path, source):
        source_path = util.strip_trailing_path(source_path)
        link = self._link_path(source_path, source)
        _symlink(source_path, link)

    def _link_path(self, source_path, source):
        basename = os.path.basename(source_path)
        res_path = self.resdef.path or ""
        if os.path.isabs(res_path):
            raise DependencyError(
                "invalid path '%s' in %s resource (path must be relative)"
                % (res_path, self.resdef.name))
        if source.rename:
            basename = _rename_source(basename, source.rename)
        return os.path.join(self.ctx.target_dir, res_path, basename)

def _rename_source(name, rename):
    for spec in rename:
        pattern, repl = _split_rename_spec(spec)
        try:
            renamed = re.sub(pattern, repl, name)
        except Exception as e:
            raise DependencyError(
                "error renaming source %s (%r %r): %s"
                % (name, pattern, repl, e))
        else:
            if renamed != name:
                return renamed
    return name

def _split_rename_spec(spec):
    spec = spec or "" # shlex.split hangs forever on None
    parts = shlex.split(spec)
    if len(parts) != 2:
        raise DependencyError(
            "invalid rename spec: %s - expected 'PATTERN REPL'"
            % spec)
    return parts

def _symlink(source_path, link):
    assert os.path.isabs(link), link
    if os.path.exists(link):
        log.warning("%s already exists, skipping link", link)
        return
    util.ensure_dir(os.path.dirname(link))
    log.debug("resolving source %s as link %s", source_path, link)
    util.symlink(source_path, link)

class ResourceProxy(object):

    def __init__(self, dependency, name, config, ctx):
        self.dependency = dependency
        self.name = name
        self.config = config
        self.ctx = ctx

    def resolve(self):
        source_path = self.config # the only type of config supported
        if not os.path.exists(source_path):
            raise DependencyError(
                "could not resolve %s: %s does not exist"
                % (self.name, source_path))
        log.info("Using %s for %s resource", source_path, self.name)
        basename = os.path.basename(source_path)
        link = os.path.join(self.ctx.target_dir, basename)
        _symlink(source_path, link)
        return [source_path]

def _dep_desc(dep):
    return "%s:%s" % (dep.opdef.modeldef.name, dep.opdef.name)

def resolve(dependencies, ctx):
    resolved = {}
    for res in resources(dependencies, ctx):
        log.info("Resolving %s dependency", res.resdef.name)
        resolved_sources = res.resolve()
        log.debug(
            "resolved sources for %s: %r",
            res.dependency, resolved_sources)
        if not resolved_sources:
            log.warning("Nothing resolved for %s dependency", res.resdef.name)
        resolved.setdefault(res.resdef.name, []).extend(resolved_sources)
    return resolved

def resources(dependencies, ctx):
    flag_vals = util.resolve_all_refs(ctx.opdef.flag_values())
    return [_dependency_resource(dep, flag_vals, ctx) for dep in dependencies]

def _dependency_resource(dep, flag_vals, ctx):
    if dep.inline_resource:
        return _inline_resource(dep.inline_resource, ctx)
    spec = util.resolve_refs(dep.spec, flag_vals)
    try:
        res = util.find_apply(
            [_model_resource,
             _guildfile_resource,
             _packaged_resource],
            spec, ctx)
    except DependencyError as e:
        if spec in ctx.resource_config:
            log.warning("%s", e)
            return ResourceProxy(dep, spec, ctx.resource_config[spec], ctx)
        raise
    if res:
        res.dependency = spec
        return res
    raise DependencyError(
        "invalid dependency '%s' in operation '%s'"
        % (spec, ctx.opdef.fullname))

def _inline_resource(resdef, ctx):
    return Resource(resdef, resdef.modeldef.guildfile.dir, ctx)

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
    return Resource(resdef, modeldef.guildfile.dir, ctx)

def _guildfile_resource(spec, ctx):
    m = re.match(r"(%s):(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = ctx.opdef.guildfile.models.get(model_name)
    if modeldef is None:
        raise DependencyError(
            "model '%s' in resource '%s' required by operation "
            "'%s' is not defined"
            % (model_name, spec, ctx.opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, ctx)

def _packaged_resource(spec, ctx):
    m = re.match(r"(%s)/(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    try:
        resources = list(resource.for_name(res_name))
    except LookupError:
        pass
    else:
        for res in resources:
            if namespace.apply_namespace(res.dist.project_name) == pkg_name:
                location = os.path.join(
                    res.dist.location,
                    res.dist.key.replace(".", os.path.sep))
                return Resource(res.resdef, location, ctx)
    raise DependencyError(
        "resource '%s' required by operation '%s' is not installed"
        % (spec, ctx.opdef.fullname))
