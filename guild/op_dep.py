# Copyright 2017-2020 TensorHub, Inc.
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

import os
import re
import logging

from guild import namespace
from guild import resolver as resolverlib
from guild import resourcedef
from guild import resource as reslib
from guild import util

log = logging.getLogger("guild")

RES_TERM = r"[a-zA-Z0-9_\-\.]+"

MODEL_RES_P = re.compile(r"(%s)$" % RES_TERM)
GUILDFILE_RES_P = re.compile(r"(%s):(%s)$" % (RES_TERM, RES_TERM))
PACKAGE_RES_P = re.compile(r"(%s)/(%s)$" % (RES_TERM, RES_TERM))

###################################################################
# Exception classes
###################################################################


class OpDependencyError(Exception):
    pass


###################################################################
# State
###################################################################


class OpDependency(object):
    def __init__(self, resdef, res_location, config):
        self.resdef = resdef
        self.res_location = res_location
        self.config = config


###################################################################
# Deps for opdef
###################################################################


def deps_for_opdef(opdef, flag_vals):
    return [_init_dep(depdef, flag_vals) for depdef in opdef.dependencies]


def _init_dep(depdef, flag_vals):
    resdef, res_location = resource_def(depdef, flag_vals)
    config = _resdef_config(resdef, flag_vals)
    return OpDependency(resdef, res_location, config)


def _resdef_config(resdef, flag_vals):
    for name in [resdef.fullname, resdef.name]:
        try:
            return flag_vals[name]
        except KeyError:
            pass
    return None


def resource_def(depdef, flag_vals):
    resdef, res_location = _resdef_for_dep(depdef, flag_vals)
    _resolve_source_refs(resdef, flag_vals)
    return resdef, res_location


def _resdef_for_dep(depdef, flag_vals):
    if depdef.inline_resource:
        return depdef.inline_resource, depdef.opdef.guildfile.dir
    res_spec = util.resolve_refs(depdef.spec, flag_vals)
    return util.find_apply(
        [
            _model_resource,
            _guildfile_resource,
            _package_resource,
            _invalid_dependency_error,
        ],
        res_spec,
        depdef,
    )


def _model_resource(spec, depdef):
    m = MODEL_RES_P.match(spec)
    if m is None:
        return None
    res_name = m.group(1)
    return _modeldef_resource(depdef.modeldef, res_name, depdef.opdef)


def _modeldef_resource(modeldef, res_name, opdef):
    resdef = modeldef.get_resource(res_name)
    if resdef is None:
        raise OpDependencyError(
            "resource '%s' required by operation '%s' is not defined"
            % (res_name, opdef.fullname)
        )
    return resdef, modeldef.guildfile.dir


def _guildfile_resource(spec, depdef):
    m = GUILDFILE_RES_P.match(spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = depdef.opdef.guildfile.models.get(model_name)
    if modeldef is None:
        raise OpDependencyError(
            "model '%s' in resource '%s' required by operation "
            "'%s' is not defined" % (model_name, spec, depdef.opdef.fullname)
        )
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, depdef.opdef)


def _package_resource(spec, depdef):
    m = PACKAGE_RES_P.match(spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    res = _find_package_resource(pkg_name, res_name)
    if not res:
        raise OpDependencyError(
            "resource '%s' required by operation '%s' is not installed"
            % (spec, depdef.opdef.fullname)
        )
    return res.resdef, _package_res_location(res)


def _find_package_resource(pkg_name, res_name):
    try:
        resources = list(reslib.for_name(res_name))
    except LookupError:
        return None
    else:
        for res in resources:
            if namespace.apply_namespace(res.dist.project_name) == pkg_name:
                return res
        return None


def _package_res_location(res):
    return os.path.join(res.dist.location, res.dist.key.replace(".", os.path.sep))


def _invalid_dependency_error(spec, depdef):
    raise OpDependencyError(
        "invalid dependency '%s' in operation '%s'" % (spec, depdef.opdef.fullname)
    )


def _resolve_source_refs(resdef, flag_vals):
    for source in resdef.sources:
        source.uri = _resolve_dep_attr_refs(source.uri, flag_vals, resdef)
        source.rename = _resolve_rename_spec_refs(source.rename, flag_vals, resdef)


def _resolve_dep_attr_refs(attr_val, flag_vals, resdef):
    try:
        return util.resolve_refs(attr_val, flag_vals)
    except util.UndefinedReferenceError as e:
        raise OpDependencyError(
            "invalid flag reference '%s' in dependency '%s'"
            % (resdef.name, e.reference)
        )


def _resolve_rename_spec_refs(specs, flag_vals, resdef):
    if not specs:
        return specs
    return [
        resourcedef.RenameSpec(
            _resolve_dep_attr_refs(spec.pattern, flag_vals, resdef),
            _resolve_dep_attr_refs(spec.repl, flag_vals, resdef),
        )
        for spec in specs
    ]


###################################################################
# Resolve support
###################################################################


def ResolveContext(run):
    """Interface between op resolution and resolve context.

    We maintain this interface keep op_dep and its implementation
    separate.
    """
    return resolverlib.ResolveContext(run=run, unpack_dir=None)


def resolve_source(source, dep, resolve_context):
    last_resolution_error = None
    for location in _dep_resource_locations(dep):
        try:
            source_paths = _resolve_source_for_location(
                source, dep, location, resolve_context
            )
        except resolverlib.ResolutionError as e:
            last_resolution_error = e
        except Exception as e:
            _unknown_source_resolution_error(source, dep, e)
        else:
            for path in source_paths:
                _link_to_source(path, source, resolve_context.run.dir)
            return source_paths
    assert last_resolution_error
    _source_resolution_error(source, dep, last_resolution_error)


def _dep_resource_locations(dep):
    yield dep.res_location
    for parent in dep.resdef.modeldef.parents:
        yield parent.dir


def _resolve_source_for_location(source, dep, location, resolve_context):
    res_proxy = _ResourceProxy(location, dep.config)
    resolver = resolverlib.for_resdef_source(source, res_proxy)
    if not resolver:
        raise OpDependencyError(
            "unsupported source '%s' in %s resource" % (source, dep.resdef.name)
        )
    return resolver.resolve(resolve_context)


def resolver_for_source(source, dep):
    res_proxy = _ResourceProxy(dep.res_location, dep.config)
    return resolverlib.for_resdef_source(source, res_proxy)


class _ResourceProxy(object):
    """Proxy for guild.deps.Resource, used by resolver API.

    The APIs in guild.deps and guild.resolver are to be replaced by
    this module and a new resolver interface. Until the new resolver
    interface is created, we use a proxy resource to work with the
    current interface.
    """

    def __init__(self, location, config):
        self.location = location
        self.config = config


def _source_resolution_error(source, dep, e):
    msg = "could not resolve '%s' in %s resource: %s" % (source, dep.resdef.name, e)
    if source.help:
        msg += "\n%s" % source.help
    raise OpDependencyError(msg)


def _unknown_source_resolution_error(source, dep, e):
    log.exception(
        "resolving required source '%s' in %s resource", source, dep.resdef.name
    )
    raise OpDependencyError(
        "unexpected error resolving '%s' in %s resource: %r"
        % (source, dep.resdef.name, e)
    )


def _link_to_source(source_path, source, target_dir):
    source_path = util.strip_trailing_sep(source_path)
    link = _link_path(source_path, source, target_dir)
    _symlink(source_path, link)


def _link_path(source_path, source, target_dir):
    basename = os.path.basename(source_path)
    res_path = source.resdef.path or ""
    if source.path:
        res_path = os.path.join(res_path, source.path)
    if os.path.isabs(res_path):
        raise OpDependencyError(
            "invalid path '%s' in %s resource (path must be relative)"
            % (res_path, source.resdef.name)
        )
    if source.rename:
        basename = _rename_source(basename, source.rename)
    return os.path.join(target_dir, res_path, basename)


def _rename_source(name, rename):
    for spec in rename:
        try:
            renamed = re.sub(spec.pattern, spec.repl, name, count=1)
        except Exception as e:
            raise OpDependencyError(
                "error renaming source %s (%r %r): %s"
                % (name, spec.pattern, spec.repl, e)
            )
        else:
            if renamed != name:
                return renamed
    return name


def _symlink(source_path, link):
    assert os.path.isabs(link), link
    if os.path.lexists(link) or os.path.exists(link):
        log.warning("%s already exists, skipping link", link)
        return
    util.ensure_dir(os.path.dirname(link))
    log.debug("resolving source %s as link %s", source_path, link)
    rel_source_path = _rel_source_path(source_path, link)
    util.symlink(rel_source_path, link)


def _rel_source_path(source, link):
    source_dir, source_name = os.path.split(source)
    real_link = util.realpath(link)
    link_dir = os.path.dirname(real_link)
    source_rel_dir = os.path.relpath(source_dir, link_dir)
    return os.path.join(source_rel_dir, source_name)


###################################################################
# Op run resolve support
###################################################################


def resolved_op_runs_for_opdef(opdef, flag_vals):
    try:
        deps = deps_for_opdef(opdef, flag_vals)
    except OpDependencyError as e:
        log.debug("error resolving runs for opdef: %s", e)
        return []
    else:
        return list(_iter_resolved_op_runs(deps, flag_vals))


def _iter_resolved_op_runs(deps, flag_vals):
    for dep in deps:
        for source in dep.resdef.sources:
            if not source.uri.startswith("operation:"):
                continue
            resolver = resolver_for_source(source, dep)
            assert isinstance(resolver, resolverlib.OperationResolver), resolver
            run_id_prefix = flag_vals.get(dep.resdef.name)
            try:
                run = resolver.resolve_op_run(run_id_prefix, include_staged=True)
            except resolverlib.ResolutionError:
                log.warning(
                    "cannot find a suitable run for required " "resource '%s'",
                    dep.resdef.name,
                )
            else:
                yield run, dep
