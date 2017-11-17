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

import errno
import logging
import os
import re

import yaml

from guild import resolve
from guild import resourcedef

log = logging.getLogger("core")

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
        return self.models[0] if self.models else None

###################################################################
# Includes support
###################################################################

def _resolve_includes(data, section_name, modelfile, coerce_data):
    assert isinstance(data, dict), data
    resolved = {}
    seen_includes = set()
    section_data = data.get(section_name, {})
    if isinstance(section_data, str):
        includes = _parse_use_stmt(section_data, section_name, modelfile)
        _apply_includes(
            includes,
            modelfile,
            section_name,
            coerce_data,
            seen_includes,
            resolved)
    elif isinstance(section_data, dict):
        _apply_section_data(
            section_data,
            modelfile,
            section_name,
            coerce_data,
            seen_includes,
            resolved)
    else:
        raise ModelfileFormatError(
            "invalid %s data: %s" % (section_name, data))
    return resolved

def _parse_use_stmt(s, section_name, modelfile):
    m = re.match("use (.+)", s.strip())
    if not m:
        raise ModelfileFormatError(
            "invalid string value for for '%s' in %s: expected 'use ...'"
            % (section_name, modelfile.src))
    return [part.strip() for part in m.group(1).split(",")]

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

def _apply_section_data(data, modelfile, section_name, coerce_data,
                        seen_includes, resolved):
    for name in _includes_first(data):
        if name == "$include":
            _apply_includes(
                data[name].split(),
                modelfile,
                section_name,
                coerce_data,
                seen_includes,
                resolved)
        else:
            _apply_data(name, data[name], resolved, coerce_data)

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

    def flag_values(self):
        return dict(self._iter_flag_values())

    def _iter_flag_values(self):
        seen = set()
        for name in self._flag_vals:
            yield name, self._flag_vals[name]
            seen.add(name)
        if self._parent:
            for name in self._parent._flag_vals:
                if name not in seen:
                    yield name, self._parent._flag_vals[name]
                    seen.add(name)

    def set_flag_value(self, name, val):
        self._flag_vals[name] = val

    def get_flag_value(self, name, default=None):
        try:
            return self._flag_vals[name]
        except KeyError:
            return (self._parent.get_flag_val(name)
                    if self._parent
                    else default)

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
        return {"value": data}
    else:
        raise ModelfileFormatError("unsupported flag data: %s" % data)

class FlagDef(object):

    def __init__(self, name, data):
        self.name = name
        self.value = data.get("value")
        self.description = data.get("description", "")
        self.required = bool(data.get("required"))
        self.arg_name = data.get("arg-name")
        self.options = _init_flag_options(data.get("options"))

def _init_flag_values(flagdefs):
    return {
        flag.name: flag.value
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
        super(ModelDef, self).__init__(data, modelfile)
        self.modelfile = modelfile
        self.name = data.get("name")
        self.description = data.get("description", "").strip()
        self.private = bool(data.get("private"))
        self.operations = _init_ops(data.get("operations", {}), self)
        self.resources = _init_resources(data.get("resources", {}), self)
        self.disabled_plugins = data.get("disabled-plugins", [])

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
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.dependencies = _init_dependencies(data.get("requires"), self)

    def __repr__(self):
        return "<guild.modelfile.OpDef '%s'>" % self.fullname

    @property
    def fullname(self):
        return "%s:%s" % (self.modeldef.name, self.name)

def _init_dependencies(requires, opdef):
    if not requires:
        return []
    if isinstance(requires, str):
        requires = [requires]
    return [OpDependency(spec, opdef) for spec in requires]

class OpDependency(object):

    def __init__(self, spec, opdef):
        self.spec = spec
        self.opdef = opdef

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

    def get_source_resolver(self, source):
        scheme = source.parsed_uri.scheme
        if scheme == "file":
            return resolve.FileResolver(source, self.modeldef.modelfile.dir)
        elif scheme == "operation":
            return resolve.OperationOutputResolver(source, self.modeldef)
        else:
            return super(ResourceDef, self).get_source_resolver(source)

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
    return Modelfile(yaml.load(open(src, "r")), src)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise

def from_string(s, src):
    return Modelfile(yaml.load(s), src)
