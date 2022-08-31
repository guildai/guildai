# Copyright 2017-2022 RStudio, PBC
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

import os
import re
import logging
import typing

from guild import cli
from guild import resolver as resolverlib
from guild import resourcedef
from guild import util

log = logging.getLogger("guild")

RES_TERM = r"[a-zA-Z0-9_\-\.]+"

MODEL_RES_P = re.compile(rf"({RES_TERM})$")
GUILDFILE_RES_P = re.compile(rf"({RES_TERM}):({RES_TERM})$")
PACKAGE_RES_P = re.compile(rf"({RES_TERM})/({RES_TERM})$")

DEFAULT_TARGET_TYPE = "copy"

###################################################################
# Exception classes
###################################################################


class OpDependencyError(Exception):
    pass


###################################################################
# State
###################################################################


class OpDependency:
    def __init__(self, resdef, res_location, config):
        assert res_location
        self.resdef = resdef
        self.res_location = res_location
        self.config = config


###################################################################
# Deps for opdef
###################################################################


def deps_for_opdef(opdef, flag_vals):
    return [dep_for_depdef(depdef, flag_vals) for depdef in opdef.dependencies]


def dep_for_depdef(depdef, flag_vals):
    resdef, res_location = resource_def(depdef, flag_vals)
    config = _resdef_config(resdef, flag_vals)
    return OpDependency(resdef, res_location, config)


def _resdef_config(resdef, flag_vals):
    for name in [resdef.fullname, (resdef.flag_name or resdef.name)]:
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
            f"resource '{res_name}' required by operation "
            f"'{opdef.fullname}' is not defined"
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
            f"model '{model_name}' in resource '{spec}' required by operation "
            f"'{depdef.opdef.fullname}' is not defined"
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
            f"resource '{spec}' required by operation "
            f"'{depdef.opdef.fullname}' is not installed"
        )
    return res.resdef, _package_res_location(res)


def _find_package_resource(pkg_name, res_name):
    from guild import namespace  # expensive
    from guild import resource as reslib  # expensive

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
        f"invalid dependency '{spec}' in operation '{depdef.opdef.fullname}'"
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
            f"invalid flag reference '{resdef.name}' in dependency '{e.reference}'"
        ) from e


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
# Dep constructors
###################################################################


def dep_for_path(path, resource_name=None):
    res_data = {
        "sources": [{"file": path}],
        "target-type": "link",
    }
    resource_name = resource_name or f"file:{path}"
    resdef = resourcedef.ResourceDef(resource_name, res_data)
    return OpDependency(resdef, res_location=".", config=None)


###################################################################
# Resolve support
###################################################################


def ResolveContext(run):
    """Interface between op resolution and resolve context.

    We maintain this interface keep op_dep and its implementation
    separate.
    """
    return resolverlib.ResolveContext(run=run, unpack_dir=None)


def resolve_source(source, dep, resolve_context, resolve_cb=None):
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
                resolved = _resolve_source_for_path(
                    path,
                    location,
                    source,
                    resolve_context.run.dir,
                )
                _handle_resolved_source(resolved, resolve_cb)
            return source_paths
    assert last_resolution_error
    _source_resolution_error(source, dep, last_resolution_error)


def _handle_resolved_source(resolved, resolve_cb):
    if resolved and resolve_cb:
        resolve_cb(resolved)


def _dep_resource_locations(dep):
    yield dep.res_location
    if hasattr(dep.resdef, "modeldef") and dep.resdef.modeldef:
        for parent in dep.resdef.modeldef.parents:
            yield parent.dir


def _resolve_source_for_location(source, dep, location, resolve_context):
    res_proxy = ResourceProxy(location, dep.config)
    resolver = resolverlib.for_resdef_source(source, res_proxy)
    if not resolver:
        raise OpDependencyError(
            f"unsupported source '{source}' in {dep.resdef.name} resource"
        )
    return resolver.resolve(resolve_context)


def resolver_for_source(source, dep):
    res_proxy = ResourceProxy(dep.res_location, dep.config)
    return resolverlib.for_resdef_source(source, res_proxy)


class ResourceProxy:
    """Proxy for guild.deps.Resource, used by resolver API.

    The APIs in guild.deps and guild.resolver are to be replaced by
    this module and a new resolver interface. Until the new resolver
    interface is created, we use a proxy resource to work with the
    current interface.
    """

    def __init__(self, location, config):
        assert location
        self.location = location
        self.config = config


def _source_resolution_error(source, dep, e) -> typing.NoReturn:
    msg = f"could not resolve '{source}' in {dep.resdef.name} resource: {e}"
    if source.help:
        msg += "\n" + cli.style(source.help, fg="yellow")
    raise OpDependencyError(msg)


def _unknown_source_resolution_error(source, dep, e):
    log.exception(
        "resolving required source '%s' in %s resource", source, dep.resdef.name
    )
    raise OpDependencyError(
        f"unexpected error resolving '{source}' in {dep.resdef.name} resource: {e!r}"
    )


class ResolvedSource:
    def __init__(
        self,
        source,
        target_path,
        target_root,
        source_path,
        source_origin,
    ):
        self.source = source
        self.target_path = target_path
        self.target_root = target_root
        self.source_path = source_path
        self.source_origin = source_origin


def _resolve_source_for_path(source_path, source_origin, source, target_dir):
    target_type = _target_type_for_source(source)
    target_path = _target_path_for_source(
        source_path, source_origin, source, target_dir
    )
    if util.compare_paths(source_path, target_path):
        # Source was resolved directly to run dir - nothing to do.
        return None
    if target_type == "link":
        _link_to_source(source_path, target_path, source.replace_existing)
    elif target_type == "copy":
        _copy_source(source_path, target_path, source.replace_existing)
    else:
        assert False, (target_type, source, source.resdef)
    return ResolvedSource(
        source,
        target_path,
        target_dir,
        source_path,
        source_origin,
    )


def _target_type_for_source(source):
    if source.target_type:
        return _validate_target_type(source.target_type, f"source {source.name}")
    if source.resdef.target_type:
        return _validate_target_type(
            source.resdef.target_type, f"resource {source.resdef.name}"
        )
    return DEFAULT_TARGET_TYPE


def _validate_target_type(val, desc):
    if val in ("link", "copy"):
        return val
    raise OpDependencyError(
        f"unsupported target-type '{val}' in {desc} (expected 'link' or 'copy')"
    )


def _target_path_for_source(source_path, source_origin, source, target_dir):
    """Returns target path for source.

    If target path is defined for the source, it redefines any value
    defined for the resource parent.
    """
    target_path = _source_target_path(source, source_path, source_origin)
    if os.path.isabs(target_path):
        raise OpDependencyError(
            f"invalid path '{target_path}' in {source.resdef.name} resource "
            "(path must be relative)"
        )
    basename = os.path.basename(source_path)
    if source.rename:
        basename = _rename_source(basename, source.rename)
    return os.path.join(target_dir, target_path, basename)


def _source_target_path(source, source_path, source_origin):
    target_path_attr = source.target_path or source.resdef.target_path
    if source.preserve_path:
        if target_path_attr:
            log.warning(
                "target-path '%s' specified with preserve-path - ignoring",
                target_path_attr,
            )
        return os.path.relpath(os.path.dirname(source_path), source_origin)
    return target_path_attr or source.resdef.target_path or ""


def _link_to_source(source_path, link, replace_existing=False):
    assert os.path.isabs(link), link
    source_path = util.strip_trailing_sep(source_path)
    if os.path.lexists(link) or os.path.exists(link):
        if not replace_existing:
            log.warning("%s already exists, skipping link", link)
            return
        log.debug("deleting existing source link %s", link)
        util.safe_rmtree(link)
    util.ensure_dir(os.path.dirname(link))
    log.debug("resolving source %s as link %s", source_path, link)
    source_rel_path = _source_rel_path(source_path, link)
    try:
        util.symlink(source_rel_path, link)
    except OSError as e:
        _handle_source_link_error(e)


def _source_rel_path(source, link):
    source_dir, source_name = os.path.split(source)
    real_link = util.realpath(link)
    link_dir = os.path.dirname(real_link)
    source_rel_dir = os.path.relpath(source_dir, link_dir)
    return os.path.join(source_rel_dir, source_name)


def _handle_source_link_error(e):
    raise OpDependencyError(f"unable to link to dependency source: {e}")


def _rename_source(name, rename):
    for spec in rename:
        try:
            renamed = re.sub(spec.pattern, spec.repl, name, count=1)
        except Exception as e:
            raise OpDependencyError(
                f"error renaming source {name} ({spec.pattern!r} {spec.repl!r}): {e}"
            ) from e
        else:
            if renamed != name:
                return renamed
    return name


def _copy_source(source_path, dest_path, replace_existing=False):
    assert os.path.isabs(dest_path), dest_path
    if os.path.lexists(dest_path) or os.path.exists(dest_path):
        if not replace_existing:
            log.warning("%s already exists, skipping copy", dest_path)
            return
        log.debug("deleting existing source dest %s", dest_path)
        util.safe_rmtree(dest_path)
    util.ensure_dir(os.path.dirname(dest_path))
    log.debug("resolving source %s as copy %s", source_path, dest_path)
    if os.path.isdir(source_path):
        util.copytree(source_path, dest_path)
    else:
        util.copyfile(source_path, dest_path)


###################################################################
# Op run resolve support
###################################################################


def resolved_op_runs_for_opdef(opdef, flag_vals, resolver_factory=None):
    """Returns a list of run, dep tuples for resolved run deps for opdef."""
    try:
        deps = deps_for_opdef(opdef, flag_vals)
    except OpDependencyError as e:
        log.debug("error resolving runs for opdef: %s", e)
        return []
    else:
        return list(_iter_resolved_op_runs(deps, flag_vals, resolver_factory))


def _iter_resolved_op_runs(deps, flag_vals, resolver_factory=None):
    resolver_factory = resolver_factory or resolver_for_source
    for dep in deps:
        for source in dep.resdef.sources:
            if not is_operation_source(source):
                continue
            resolver = resolver_factory(source, dep)
            assert isinstance(resolver, resolverlib.OperationResolver), resolver
            for run_id_prefix in _iter_flag_val_items(flag_vals.get(dep.resdef.name)):
                try:
                    run = resolver.resolve_op_run(run_id_prefix, include_staged=True)
                except resolverlib.ResolutionError:
                    log.warning(
                        "cannot find a suitable run for required resource '%s'",
                        dep.resdef.name,
                    )
                else:
                    yield run, dep


def is_operation_source(source):
    cls = resolverlib.resolver_class_for_source(source)
    return cls is not None and issubclass(cls, resolverlib.OperationResolver)


def _iter_flag_val_items(val):
    if isinstance(val, list):
        for item in val:
            yield item
    else:
        yield val
