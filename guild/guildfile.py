# Copyright 2017-2018 TensorHub, Inc.
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
import warnings

import six
import yaml

from guild import resourcedef

log = logging.getLogger("guild")

NAMES = ["guild.yml"]

ALL_TYPES = ["model", "config", "package", "include"]
MODEL_TYPES = ["model", "config"]

_cache = {}

###################################################################
# Exceptions
###################################################################

class GuildfileError(Exception):

    def __init__(self, guildfile_or_path, msg):
        super(GuildfileError, self).__init__(guildfile_or_path, msg)
        if isinstance(guildfile_or_path, Guildfile):
            self.path = guildfile_or_path.src
        else:
            self.path = guildfile_or_path
        self.msg = msg

    def __str__(self):
        return "error in %s: %s" % (self.path, self.msg)

class NoModels(GuildfileError):

    def __init__(self, guildfile_or_path):
        super(NoModels, self).__init__(guildfile_or_path, "no models")

    def __str__(self):
        return "no models in %s" % self.path

class GuildfileReferenceError(GuildfileError):
    pass

class GuildfileCycleError(GuildfileError):

    def __init__(self, guildfile_or_path, desc, cycle):
        msg = "%s (%s)" % (desc, " -> ".join(cycle))
        super(GuildfileCycleError, self).__init__(guildfile_or_path, msg)

###################################################################
# Helpers
###################################################################

def _required(name, data, guildfile):
    try:
        return data[name]
    except KeyError:
        raise GuildfileError(
            guildfile,
            "missing required '%s' attribute in %r"
            % (name, data))

def _script_source(src):
    return re.match(r"<.*>$", src)

###################################################################
# Guildfile
###################################################################

class Guildfile(object):

    def __init__(self, data, src=None, dir=None, included=None):
        if not dir and src and not _script_source(src):
            dir = os.path.dirname(src)
        if src is None and dir is None:
            raise ValueError("either src or dir must be specified")
        self.src = src
        self.dir = dir
        self.default_model = None
        self.models = {}
        self.package = None
        data = self._coerce_data(data)
        self.data = self._expand_data_includes(data, included or [])
        try:
            self._apply_data()
        except (GuildfileError, resourcedef.ResourceFormatError):
            raise
        except Exception as e:
            log.error("loading %s: %r", self.src, e)
            raise

    def _coerce_data(self, data):
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise GuildfileError(self, "invalid guildfile data: %r" % data)

    def _expand_data_includes(self, data, included):
        i = 0
        while i < len(data):
            item = data[i]
            try:
                includes = item["include"]
            except KeyError:
                i += 1
            else:
                new_items = self._include_data(includes, included)
                data[i:i+1] = new_items
                i += len(new_items)
        return data

    def _include_data(self, includes, included):
        includes = self._coerce_data_includes(includes)
        if not _script_source(self.src):
            included.append(os.path.abspath(self.src))
        include_data = []
        for path in includes:
            path = os.path.abspath(os.path.join(self.dir or "", path))
            if path in included:
                raise GuildfileCycleError(
                    "cycle in 'includes'",
                    included[0],
                    included + [path])
            data = yaml.load(open(path, "r"))
            gf = Guildfile(data, path, included=included)
            include_data.extend(gf.data)
        return include_data

    def _coerce_data_includes(self, val):
        if isinstance(val, six.string_types):
            return [val]
        elif isinstance(val, list):
            return val
        else:
            raise GuildfileError(self, "invalid includes value: %r" % val)

    def _apply_data(self):
        for item in self.data:
            item_type, name = self._validated_item_type(item)
            if item_type == "model":
                self._apply_model(name, item)
            elif item_type == "package":
                self._apply_package(name, item)

    def _validated_item_type(self, item):
        used = [name for name in ALL_TYPES if name in item]
        if not used:
            raise GuildfileError(
                self, ("missing required type (one of: %s) in %r"
                       % (", ".join(ALL_TYPES), item)))
        elif len(used) > 1:
            raise GuildfileError(
                self, ("multiple types (%s) in %r"
                       % (", ".join(used), item)))
        validated_type = used[0]
        name = item[validated_type]
        if not isinstance(name, six.string_types):
            raise GuildfileError(
                self, ("invalid %s name: %r"
                       % (validated_type, name)))
        return validated_type, name

    def _apply_model(self, name, data):
        if name in self.models:
            raise GuildfileError(self, "duplicate model '%s'" % name)
        model = ModelDef(name, data, self)
        if not self.default_model:
            self.default_model = model
        self.models[name] = model

    def _apply_package(self, name, data):
        if self.package:
            raise GuildfileError(self, "mutiple package definitions")
        self.package = PackageDef(name, data, self)

    def __repr__(self):
        return "<guild.guildfile.Guildfile '%s'>" % self

    def __str__(self):
        return self.src or self.dir

    def __eq__(self, _x):
        raise AssertionError()

###################################################################
# Include attribute support
###################################################################

def _resolve_includes(data, section_name, guildfile, coerce_data=None):
    assert isinstance(data, dict), data
    resolved = {}
    seen_includes = set()
    section_data = data.get(section_name, {})
    _apply_section_data(
        section_data,
        guildfile,
        section_name,
        coerce_data,
        seen_includes,
        resolved)
    return resolved

def _apply_section_data(data, guildfile, section_name, coerce_data,
                        seen_includes, resolved):
    for name in _includes_first(data):
        if name == "$include":
            _apply_includes(
                _coerce_includes(data[name], guildfile),
                guildfile,
                section_name,
                coerce_data,
                seen_includes,
                resolved)
        else:
            _apply_data(name, data[name], resolved, coerce_data, guildfile)

def _coerce_includes(val, src):
    if isinstance(val, str):
        return [val]
    elif isinstance(val, list):
        return val
    else:
        raise GuildfileError(src, "invalid $include value: %r" % val)

def _apply_includes(includes, guildfile, section_name, coerce_data,
                    seen_includes, resolved):
    _assert_guildfile_data(guildfile)
    for ref in includes:
        if ref in seen_includes:
            break
        seen_includes.add(ref)
        # Have to access guildfile.data here rather than use
        # guildfile.get because guildfile may is not initialized at
        # this point.
        include_model, include_op = _split_include_ref(ref, guildfile)
        for model_data in guildfile.data:
            if _item_name(model_data, MODEL_TYPES) == include_model:
                if include_op:
                    op_data = _op_data(model_data, include_op)
                    if op_data is None:
                        raise GuildfileReferenceError(
                            guildfile,
                            "invalid include reference '%s': operation "
                            "'%s' is not defined" % (ref, include_op))
                    section_data = op_data.get(section_name, {})
                else:
                    section_data = model_data.get(section_name, {})
                _apply_section_data(
                    section_data,
                    guildfile,
                    section_name,
                    coerce_data,
                    seen_includes,
                    resolved)
                break
        else:
            raise GuildfileReferenceError(
                guildfile,
                "invalid include reference '%s': model '%s' "
                "is not defined" % (ref, include_model))

def _assert_guildfile_data(guildfile):
    # This is called by guildfile components that need to access
    # guildfile data before the modefile is fully initialized.
    assert hasattr(guildfile, "data"), "modesfile data not initialized"

def _split_include_ref(ref, src):
    parts = ref.split(":", 1)
    if len(parts) == 1:
        return parts[0], None
    else:
        if not parts[0]:
            raise GuildfileReferenceError(
                src, ("invalid include reference '%s': operation references "
                      "must be specified as MODEL:OPERATION" % ref))
        return parts

def _item_name(data, types):
    for attr in types:
        try:
            return data[attr]
        except KeyError:
            pass
    return None

def _op_data(model_data, op_name):
    return model_data.get("operations", {}).get(op_name)

def _includes_first(names):
    return sorted(names, key=lambda x: "\x00" if x == "$include" else x)

def _apply_data(name, data, resolved, coerce_data, guildfile):
    if coerce_data:
        data = coerce_data(data, guildfile)
    try:
        cur = resolved[name]
    except KeyError:
        new = {}
        new.update(data)
        resolved[name] = new
    else:
        _apply_missing_vals(cur, data)

def _apply_missing_vals(target, source):
    assert isinstance(target, dict), target
    assert isinstance(source, dict), source
    for name in source:
        target[name] = source[name]

###################################################################
# Flag support
###################################################################

class FlagHost(object):

    def __init__(self, data, guildfile, parent_host=None):
        self.flags = _init_flags(data, guildfile)
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

def _init_flags(data, guildfile):
    data = _resolve_includes(data, "flags", guildfile, _coerce_flag_data)
    return [FlagDef(name, data[name], guildfile) for name in sorted(data)]

def _coerce_flag_data(data, src):
    if isinstance(data, dict):
        return data
    elif isinstance(data, (str, int, float, bool)):
        return {"default": data}
    elif data is None:
        return {"default": None}
    else:
        raise GuildfileError(src, "invalid flag value: %r" % data)

class FlagDef(object):

    def __init__(self, name, data, guildfile):
        self.name = name
        self.guildfile = guildfile
        self.default = data.get("default")
        self.description = data.get("description", "")
        self.required = bool(data.get("required"))
        self.arg_name = data.get("arg-name")
        self.arg_skip = bool(data.get("arg-skip"))
        self.choices = _init_flag_choices(data.get("choices"), self)

    def __repr__(self):
        return "<guild.guildfile.FlagDef '%s'>" % self.name

def _init_flag_values(flagdefs):
    return {
        flag.name: flag.default
        for flag in flagdefs
    }

def _init_flag_choices(data, flagdef):
    if not data:
        return []
    return [FlagChoice(choice_data, flagdef) for choice_data in data]

class FlagChoice(object):

    def __init__(self, data, flagdef):
        self.flagdef = flagdef
        if isinstance(data, dict):
            self.value = data.get("value")
            self.description = data.get("description", "")
            self.args = data.get("args", {})
        else:
            self.value = data
            self.description = ""
            self.args = {}

###################################################################
# Model def
###################################################################

class ModelDef(FlagHost):

    def __init__(self, name, data, guildfile):
        data = _extended_data(data, guildfile)
        super(ModelDef, self).__init__(data, guildfile)
        self.name = name
        self.guildfile = guildfile
        self.description = data.get("description", "").strip()
        self.references = data.get("references", [])
        self.operations = _init_ops(data, self)
        self.resources = _init_resources(data, self)
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.extra = data.get("extra", {})

    def __repr__(self):
        return "<guild.guildfile.ModelDef '%s'>" % self.name

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

def _extended_data(config_data, guildfile, seen=None, resolve_params=True):
    seen = seen or []
    data = copy.deepcopy(config_data)
    extends = _coerce_extends(config_data.get("extends", []), guildfile)
    if extends:
        _apply_parents_data(extends, guildfile, seen, data)
    if resolve_params:
        data = _resolve_param_refs(data, data.get("params", {}))
    return data

def _coerce_extends(val, src):
    if isinstance(val, str):
        return [val]
    elif isinstance(val, list):
        return val
    else:
        raise GuildfileError(src, "invalid extends value: %r" % val)

def _apply_parents_data(extends, guildfile, seen, data):
    for name in extends:
        if name in seen:
            raise GuildfileCycleError(
                guildfile,
                "cycle in 'extends'",
                seen + [name])
        parent = _modeldef_base_data(name, guildfile)
        extended_parent = _extended_data(
            parent, guildfile, seen + [name], False)
        inheritable = [
            "description",
            "extra",
            "flags",
            "operations",
            "params",
            "references",
            "resources",
        ]
        _apply_parent_data(extended_parent, data, inheritable)

def _modeldef_base_data(name, guildfile):
    for item in guildfile.data:
        if _item_name(item, MODEL_TYPES) == name:
            return item
    raise GuildfileReferenceError(
        guildfile, "undefined model or config '%s'" % name)

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
    ops_data = data.get("operations", {})
    return [
        OpDef(key, _coerce_op_data(ops_data[key]), modeldef)
        for key in sorted(ops_data)
    ]

def _coerce_op_data(data):
    if isinstance(data, str):
        return {
            "main": data
        }
    else:
        return data

def _init_resources(data, modeldef):
    data = _resolve_includes(data, "resources", modeldef.guildfile)
    return [ResourceDef(key, data[key], modeldef) for key in sorted(data)]

###################################################################
# Op def
###################################################################

class OpDef(FlagHost):

    def __init__(self, name, data, modeldef):
        super(OpDef, self).__init__(data, modeldef.guildfile, modeldef)
        self.modeldef = modeldef
        self.guildfile = modeldef.guildfile
        self.name = name
        data = _coerce_op_data(data)
        self.description = data.get("description", "").strip()
        cmd = data.get("cmd")
        if cmd:
            warnings.warn(
                "'cmd' has been renamed to 'main' - support for 'cmd' will "
                "be removed in Guild version 0.5",
                FutureWarning, stacklevel=9999999)
            self.main = cmd
        else:
            self.main = data.get("main")
        self.plugin_op = data.get("plugin-op")
        self.disabled_plugins = data.get("disabled-plugins", [])
        self.dependencies = _init_dependencies(data.get("requires"), self)
        self.pre_process = data.get("pre-process")
        self.remote = data.get("remote", False)

    def __repr__(self):
        return "<guild.guildfile.OpDef '%s'>" % self.fullname

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
            self.spec = _required("resource", data, self.opdef.guildfile)
            self.description = data.get("description", "")
        else:
            raise GuildfileError(
                self, "invalid dependency value: %r" % data)

    def __repr__(self):
        return "<guild.guildfile.OpDependency '%s'>" % self.spec

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
        fullname = "%s:%s" % (modeldef.name, name)
        super(ResourceDef, self).__init__(name, data, fullname)
        self.private = self.private
        self.modeldef = modeldef

    def get_source_resolver(self, source, resource):
        scheme = source.parsed_uri.scheme
        if scheme == "operation":
            from guild import resolver # expensive
            return resolver.OperationOutputResolver(
                source, resource, self.modeldef)
        else:
            return super(ResourceDef, self).get_source_resolver(
                source, resource)

    def _source_for_type(self, type, val, data):
        data = self._coerce_source_data(data)
        if type == "operation":
            return resourcedef.ResourceSource(
                self, "operation:%s" % val, **data)
        else:
            return super(ResourceDef, self)._source_for_type(type, val, data)

###################################################################
# Package def
###################################################################

class PackageDef(object):

    def __init__(self, name, data, guildfile):
        self.name = name
        self.guildfile = guildfile
        self.description = data.get("description", "").strip()
        self.version = _required("version", data, guildfile)
        self.url = data.get("url")
        self.author = data.get("author")
        self.author_email = _required("author-email", data, guildfile)
        self.license = data.get("license")
        self.tags = data.get("tags", [])
        self.python_tag = data.get("python-tag")
        self.data_files = data.get("data-files", [])
        self.resources = _init_resources(data, self)
        self.python_requires = data.get("python-requires", [])
        self.requires = data.get("requires", [])

    def __repr__(self):
        return "<guild.guildfile.PackageDef '%s'>" % self.name

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
            return _load_guildfile(model_file)
    raise NoModels(path)

def dir_has_guildfile(path):
    for name in os.listdir(path):
        if name in NAMES:
            return True
    return False

def from_file(src):
    cache_key = _cache_key(src)
    cached = _cache.get(cache_key)
    if cached:
        return cached
    _cache[cache_key] = mf = _load_guildfile(src)
    return mf

def _cache_key(src):
    return os.path.abspath(src)

def _load_guildfile(src):
    return Guildfile(yaml.safe_load(open(src, "r")), src)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise

def from_string(s, src="<string>"):
    return Guildfile(yaml.safe_load(s), src)
