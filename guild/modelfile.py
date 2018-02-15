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

import copy
import errno
import logging
import os
import re

from guild import resolver
from guild import resourcedef
from guild import yaml

log = logging.getLogger("guild")

# The order here should be based on priority of selection.
NAMES = ["MODELS", "MODEL"]

_cache = {}

###################################################################
# Exceptions
###################################################################

class ModelfileError(Exception):

    def __init__(self, path):
        super(ModelfileError, self).__init__(path)
        self.path = path

class ModelfileFormatError(ModelfileError):
    pass

class NoModels(ModelfileError):
    pass

class ModelfileReferenceError(ModelfileError):
    pass

###################################################################
# Modelfile
###################################################################

class Modelfile(object):

    def __init__(self, data, src=None, dir=None):
        if src is None and dir is None:
            raise ValueError("either src or dir must be specified")
        dir = os.path.dirname(src) if src else dir
        self.src = src
        self.dir = dir
        self.data = self._coerce_modelfile_data(data)
        self.models = [
            ModelDef(model_data, self) for model_data in self.data
        ]

    def _coerce_modelfile_data(self, data):
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ModelfileFormatError(
                "invalid modelfile data in '%s': %r" % (self, data))

    def __repr__(self):
        return "<guild.modelfile.Modelfile '%s'>" % self

    def __str__(self):
        return self.src or self.dir

    def __iter__(self):
        return iter(self.models)

    def __eq__(self, _x):
        raise AssertionError()

    def get(self, model_name, default=None):
        for model in self:
            if model.name == model_name:
                return model
        return default

    def __getitem__(self, model_name):
        model = self.get(model_name)
        if model is None:
            raise KeyError(model_name)
        return model

    @property
    def default_model(self):
        for model in self.models:
            if not model.private:
                return model
        return None

###################################################################
# Includes support
###################################################################

def _resolve_includes(data, section_name, modelfile, coerce_data):
    assert isinstance(data, dict), data
    resolved = {}
    seen_includes = set()
    section_data = data.get(section_name, {})
    _apply_section_data(
        section_data,
        modelfile,
        section_name,
        coerce_data,
        seen_includes,
        resolved)
    return resolved

def _apply_section_data(data, modelfile, section_name, coerce_data,
                        seen_includes, resolved):
    for name in _includes_first(data):
        if name == "$include":
            _apply_includes(
                _coerce_includes(data[name]),
                modelfile,
                section_name,
                coerce_data,
                seen_includes,
                resolved)
        else:
            _apply_data(name, data[name], resolved, coerce_data)

def _coerce_includes(val):
    if isinstance(val, str):
        return [val]
    elif isinstance(val, list):
        return val
    else:
        raise ModelfileFormatError("invalid $include value: %r" % val)

def _apply_includes(includes, modelfile, section_name, coerce_data,
                    seen_includes, resolved):
    _assert_modelfile_data(modelfile)
    for ref in includes:
        if ref in seen_includes:
            break
        seen_includes.add(ref)
        # Have to access modelfile.data here rather than use
        # modelfile.get because modelfile may not be initialized at
        # this point.
        include_model, include_op = _split_include_ref(ref)
        for model_data in modelfile.data:
            if model_data.get("name") == include_model:
                if include_op:
                    op_data = _op_data(model_data, include_op)
                    if op_data is None:
                        raise ModelfileReferenceError(
                            "invalid include reference '%s': operation "
                            "%s is not defined" % (ref, include_op))
                    section_data = op_data.get(section_name, {})
                else:
                    section_data = model_data.get(section_name, {})
                _apply_section_data(
                    section_data,
                    modelfile,
                    section_name,
                    coerce_data,
                    seen_includes,
                    resolved)
                break
        else:
            raise ModelfileReferenceError(
                "invalid include reference '%s': model %s is not defined"
                % (ref, include_model))

def _assert_modelfile_data(modelfile):
    # This is called by modelfile components that need to access
    # modelfile data before the modefile is fully initialized.
    assert hasattr(modelfile, "data"), "modesfile data not initialized"

def _split_include_ref(ref):
    parts = ref.split(":", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        if not parts[0]:
            raise ModelfileReferenceError(
                "invalid include reference '%s': operation references must "
                "be specified as MODEL:OPERATION" % ref)
        return parts

def _op_data(model_data, op_name):
    return model_data.get("operations", {}).get(op_name)

def _includes_first(names):
    return sorted(names, key=lambda x: "\x00" if x == "$include" else x)

def _apply_data(name, data, resolved, coerce_data):
    try:
        cur = resolved[name]
    except KeyError:
        new = {}
        new.update(coerce_data(data))
        resolved[name] = new
    else:
        _apply_missing_vals(cur, coerce_data(data))

def _apply_missing_vals(target, source):
    assert isinstance(target, dict), target
    assert isinstance(source, dict), source
    for name in source:
        target[name] = source[name]

###################################################################
# Flag support
###################################################################

class FlagHost(object):

    def __init__(self, data, modelfile, parent_host=None):
        self.flags = _init_flags(data, modelfile)
        self._parent = parent_host
        self._flag_vals = _init_flag_values(self.flags)

    def get_flagdef(self, name):
        for flag in self.flags:
            if flag.name == name:
                return flag
        if self._parent:
            for flag in self._parent.flags:
                if flag.name == name:
                    return flag
        return None

    def flag_values(self, include_none=True):
        return dict(self._iter_flag_values(include_none))

    def _iter_flag_values(self, include_none):
        for name, val in self._iter_flag_values_recurse(set()):
            if val is not None or include_none:
                yield name, val

    def _iter_flag_values_recurse(self, seen):
        for name in self._flag_vals:
            if name not in seen:
                yield name, self._flag_vals[name]
                seen.add(name)
        if self._parent:
            for name, val in self._parent._iter_flag_values_recurse(seen):
                yield name, val

    def set_flag_value(self, name, val):
        self._flag_vals[name] = val

    def get_flag_value(self, name, default=None):
        try:
            return self._flag_vals[name]
        except KeyError:
            if self._parent:
                return self._parent.get_flag_value(name)
            else:
                return default

    def update_flags(self, flag_host):
        merged_map = {flag.name: flag for flag in self.flags}
        merged_map.update({flag.name: flag for flag in flag_host.flags})
        merged_flags = [merged_map[name] for name in sorted(merged_map)]
        merged_vals = {}
        merged_vals.update(self._flag_vals)
        merged_vals.update(flag_host.flag_values())
        self.flags = merged_flags
        self._flag_vals = merged_vals

def _init_flags(data, modelfile):
    flags_data = _resolve_includes(
        data,
        "flags",
        modelfile,
        _coerce_flag_data)
    return [
        FlagDef(name, flags_data[name])
        for name in sorted(flags_data)
    ]

def _coerce_flag_data(data):
    if isinstance(data, dict):
        return data
    elif isinstance(data, (str, int, float, bool)):
        return {"default": data}
    else:
        raise ModelfileFormatError("unsupported flag data: %r" % data)

class FlagDef(object):

    def __init__(self, name, data):
        self.name = name
        self.default = data.get("default")
        self.description = data.get("description", "")
        self.required = bool(data.get("required"))
        self.arg_name = data.get("arg-name")
        self.arg_skip = bool(data.get("arg-skip"))
        self.options = _init_flag_options(data.get("options"))

    def __repr__(self):
        return "<guild.modelfile.FlagDef '%s'>" % self.name

def _init_flag_values(flagdefs):
    return {
        flag.name: flag.default
        for flag in flagdefs
    }

def _init_flag_options(data):
    if not data:
        return []
    return [FlagOpt(opt_data) for opt_data in data]

class FlagOpt(object):

    def __init__(self, data):
        self.value = data.get("value")
        self.description = data.get("description", "")
        self.args = data.get("args", {})

###################################################################
# Model def
###################################################################

class ModelDef(FlagHost):

    def __init__(self, data, modelfile):
        data = _extended_data(data, modelfile.data)
        super(ModelDef, self).__init__(data, modelfile)
        self.modelfile = modelfile
        self.name = data.get("name")
        self.description = data.get("description", "").strip()
        self.references = data.get("references", [])
        self.private = bool(data.get("private"))
        self.operations = _init_ops(data.get("operations", {}), self)
        self.resources = _init_resources(data.get("resources", {}), self)
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.index_settings = data.get("index", {})

    def __repr__(self):
        return "<guild.modelfile.ModelDef '%s'>" % self.name

    def get_operation(self, name):
        for op in self.operations:
            if op.name == name:
                return op
        return None

    def get_resource(self, name):
        for res in self.resources:
            if res.name == name:
                return res
        return None

def _extended_data(modeldef_data, modelfile_data, seen=None,
                   resolve_params=True):
    seen = seen or []
    data = copy.deepcopy(modeldef_data)
    extends = _coerce_extends(modeldef_data.get("extends", []))
    if extends:
        _apply_parents_data(extends, modelfile_data, seen, data)
    if resolve_params:
        data = _resolve_param_refs(data, data.get("params", {}))
    return data

def _coerce_extends(val):
    if isinstance(val, str):
        return [val]
    elif isinstance(val, list):
        return val
    else:
        raise ModelfileFormatError(
            "invalid value for extends: %r" % val)

def _apply_parents_data(extends, modelfile_data, seen, data):
    for name in extends:
        if name in seen:
            raise ModelfileReferenceError(
                "cycle in model extends: %s" % seen)
        seen.append(name)
        parent = _modeldef_data(name, modelfile_data)
        extended_parent = _extended_data(parent, modelfile_data, seen, False)
        inheritable = [
            "description",
            "references",
            "operations",
            "flags",
            "resources",
            "params",
        ]
        _apply_parent_data(extended_parent, data, inheritable)

def _modeldef_data(name, modelfile_data):
    for modeldef_data in modelfile_data:
        if modeldef_data.get("name") == name:
            return modeldef_data
    raise ModelfileReferenceError("undefined model %s" % name)

def _apply_parent_data(parent, child, attrs=None):
    if not isinstance(child, dict) or not isinstance(parent, dict):
        return
    for name, parent_val in parent.items():
        if attrs is not None and name not in attrs:
            continue
        try:
            child_val = child[name]
        except KeyError:
            child[name] = copy.deepcopy(parent_val)
        else:
            _apply_parent_data(parent_val, child_val)

def _resolve_param_refs(val, params):
    if isinstance(val, dict):
        return _resolve_dict_param_refs(val, params)
    elif isinstance(val, list):
        return _resolve_list_param_refs(val, params)
    elif isinstance(val, str):
        return _resolve_str_param_refs(val, params)
    else:
        return val

def _resolve_dict_param_refs(d, params):
    return {
        name: _resolve_param_refs(val, params)
        for name, val in d.items()
    }

def _resolve_list_param_refs(l, params):
    return [_resolve_param_refs(x, params) for x in l]

def _resolve_str_param_refs(s, params):
    parts = [part for part in re.split(r"({{.+?}})", s) if part != ""]
    resolved = [_maybe_resolve_param_ref(part, params) for part in parts]
    if len(resolved) == 1:
        return resolved[0]
    else:
        return "".join([str(part) for part in resolved])

def _maybe_resolve_param_ref(val, params):
    if val.startswith("{{") and val.endswith("}}"):
        ref_name = val[2:-2]
        try:
            ref_val = params[ref_name]
        except KeyError:
            pass
        else:
            val = ref_val
    return val

def _init_ops(data, modeldef):
    return [
        OpDef(key, _coerce_op_data(data[key]), modeldef)
        for key in sorted(data)
    ]

def _coerce_op_data(data):
    if isinstance(data, str):
        return {
            "cmd": data
        }
    else:
        return data

def _init_resources(data, modeldef):
    return [
        ResourceDef(key, data[key], modeldef)
        for key in sorted(data)
    ]

###################################################################
# Op def
###################################################################

class OpDef(FlagHost):

    def __init__(self, name, data, modeldef):
        super(OpDef, self).__init__(data, modeldef.modelfile, modeldef)
        self.modeldef = modeldef
        self.modelfile = modeldef.modelfile
        self.name = name
        data = _coerce_op_data(data)
        self.description = data.get("description", "").strip()
        self.cmd = data.get("cmd")
        self.plugin_op = data.get("plugin-op")
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.dependencies = _init_dependencies(data.get("requires"), self)
        self.remote = data.get("remote", False)

    def __repr__(self):
        return "<guild.modelfile.OpDef '%s'>" % self.fullname

    @property
    def fullname(self):
        return "%s:%s" % (self.modeldef.name, self.name)

    def update_dependencies(self, opdef):
        self.dependencies.extend(opdef.dependencies)

def _init_dependencies(requires, opdef):
    if not requires:
        return []
    if isinstance(requires, str):
        requires = [requires]
    return [OpDependency(data, opdef) for data in requires]

class OpDependency(object):

    def __init__(self, data, opdef):
        self.opdef = opdef
        if isinstance(data, str):
            self.spec = data
            self.description = ""
        elif isinstance(data, dict):
            self.spec = data.get("resource")
            if not self.spec:
                raise ModelfileFormatError(
                    "missing required 'resource' attribute in dependency %r"
                    % data)
            self.description = data.get("description", "")
        else:
            raise ModelfileFormatError(
                "unsupported data for dependency: %r" % data)

    def __repr__(self):
        return "<guild.modelfile.OpDependency '%s'>" % self.spec

class NoSuchResourceError(ValueError):

    def __init__(self, name, dep):
        super(NoSuchResourceError, self).__init__(
            "resource '%s' is not defined in model '%s'"
            % (name, dep.opdef.modeldef.name))
        self.resource_name = name
        self.dependency = dep

###################################################################
# Resource def
###################################################################

class ResourceDef(resourcedef.ResourceDef):

    source_types = resourcedef.ResourceDef.source_types + ["operation"]

    def __init__(self, name, data, modeldef):
        super(ResourceDef, self).__init__(name, data)
        self.fullname = "%s:%s" % (modeldef.name, name)
        self.private = self.private or modeldef.private
        self.modeldef = modeldef

    def get_source_resolver(self, source, config=None):
        scheme = source.parsed_uri.scheme
        if scheme == "file":
            return resolver.FileResolver(
                source, config, self.modeldef.modelfile.dir)
        elif scheme == "operation":
            return resolver.OperationOutputResolver(
                source, config, self.modeldef)
        else:
            return super(ResourceDef, self).get_source_resolver(
                source, config)

    def _source_for_type(self, type, val, data):
        if type == "operation":
            return resourcedef.ResourceSource(
                self, "operation:%s" % val, **data)
        else:
            return super(ResourceDef, self)._source_for_type(type, val, data)

###################################################################
# Module API
###################################################################

def from_dir(path, filenames=None):
    log.debug("checking '%s' for model sources", path)
    filenames = NAMES if filenames is None else filenames
    for name in filenames:
        model_file = os.path.abspath(os.path.join(path, name))
        if os.path.isfile(model_file):
            log.debug("found model source '%s'", model_file)
            return _load_modelfile(model_file)
    raise NoModels(path)

def dir_has_modelfile(path):
    for name in os.listdir(path):
        if name in NAMES:
            return True
    return False

def from_file(src):
    cache_key = _cache_key(src)
    cached = _cache.get(cache_key)
    if cached:
        return cached
    _cache[cache_key] = mf = _load_modelfile(src)
    return mf

def _cache_key(src):
    return os.path.abspath(src)

def _load_modelfile(src):
    return Modelfile(yaml.safe_load(open(src, "r")), src)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise

def from_string(s, src="<string>"):
    return Modelfile(yaml.safe_load(s), src)
