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

import yaml

import guild.plugin

from guild import util

# The order here should be based on priority of selection.
NAMES = ["MODELS", "MODEL"]

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

    def __init__(self, data, src):
        self.data = _coerce_modelfile_data(data, src)
        self.src = src
        self.models = [
            ModelDef(model_data, self) for model_data in self.data
        ]

    def __repr__(self):
        return "<guild.modelfile.Modelfile %r>" % self.src

    def __str__(self):
        return self.src

    def __iter__(self):
        return iter(self.models)

    def __eq__(self, x):
        if isinstance(x, Modelfile):
            return os.path.abspath(self.src) == os.path.abspath(x.src)
        return False

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

def _coerce_modelfile_data(data, src):
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        raise ModelfileFormatError("invalid modelfile '%s'" % src)

###################################################################
# Includes support
###################################################################

def _resolve_includes(data, section_name, modelfile, coerce_data):
    assert isinstance(data, dict), data
    resolved = {}
    seen_includes = set()
    section_data = data.get(section_name, {})
    if isinstance(section_data, str):
        _apply_includes(
            section_data.split(),
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
        for model_data in modelfile.data:
            if model_data.get("name") == ref:
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
                "model '%s' for include doesn't exist" % ref)

def _assert_modelfile_data(modelfile):
    # This is called by modelfile components that need to access
    # modelfile data before the modefile is fully initialized.
    assert hasattr(modelfile, "data"), "modesfile data not initialized"

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
        return None

    def flag_values(self):
        return dict(self._iter_flag_values())

    def _iter_flag_values(self):
        seen = set()
        for name in self._flag_vals:
            yield name, self._flag_vals[name]
            seen.add(name)
        if self._parent:
            # pylint: disable=protected-access
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

def _init_flag_values(flagdefs):
    return {
        flag.name: flag.value
        for flag in flagdefs
    }

###################################################################
# Model def
###################################################################

class Visibility(object):

    public = "public"
    private = "private"

class ModelDef(FlagHost):

    def __init__(self, data, modelfile):
        super(ModelDef, self).__init__(data, modelfile)
        self.modelfile = modelfile
        self.name = data.get("name")
        self.description = data.get("description", "").strip()
        self.visibility = data.get("visibility", Visibility.public)
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

# TODO: need to move this to resourcedef as we add support for
# resources defined in packages - or otherwise resolve resources that
# aren't associated with a model.

class ResourceDef(object):

    def __init__(self, name, data, modeldef):
        self.name = name
        self.modeldef = modeldef
        self.modelfile = modeldef.modelfile
        self.description = data.get("description", "")
        self.sources = _init_sources(data.get("sources", []), self)

    def __repr__(self):
        return "<guild.modelfile.ResourceDef '%s'>" % self.name

    @property
    def fullname(self):
        return "%s:%s" % (self.modeldef.name, self.name)

def _init_sources(data, resdef):
    if isinstance(data, list):
        return [_init_resource_source(src_data, resdef) for src_data in data]
    elif isinstance(data, str):
        return [_init_resource_source(data, resdef)]
    else:
        raise ModelfileFormatError(
            "invalid sources for resource '%s'"
            % resdef.fullname)

def _init_resource_source(data, resdef):
    if isinstance(data, dict):
        file_path = data.get("file")
        url = data.get("url")
        if file_path and url:
            raise ModelfileFormatError(
                "invalid source in resource '%s': cannot specify "
                "both file and url" % resdef.fullname)
        if file_path:
            return FileSource(resdef, **data)
        elif url:
            return URLSource(resdef, **data)
        else:
            raise ModelfileFormatError(
                "missing source file or url in resource '%s'"
                % resdef.fullname)
    elif isinstance(data, str):
        return FileSource(resdef, data)
    else:
        raise ModelfileFormatError(
            "invalid source for resource '%s': %s"
            % (resdef.fullname, data))

class ResourceSource(object):

    def __init__(self, resdef, sha256=None, file_type=None, unpack=None, **kw):
        self.resdef = resdef
        self.sha256 = sha256
        self.file_type = file_type
        self.unpack = unpack
        for key in kw:
            logging.warning(
                "unexpected source attribute '%s' in resource '%s'",
                key, resdef.fullname)

class FileSource(ResourceSource):

    def __init__(self, resdef, file, **kw):
        super(FileSource, self).__init__(resdef, **kw)
        self.path = file

    def __repr__(self):
        return "<guild.modelfile.FileSource '%s'>" % self.path

class URLSource(ResourceSource):

    def __init__(self, resdef, url, **kw):
        super(URLSource, self).__init__(resdef, **kw)
        self.url = url

    def __repr__(self):
        return "<guild.modelfile.URLSource '%s'>" % self.url

###################################################################
# Module API
###################################################################

def from_dir(path, filenames=None, use_plugins=True):
    filenames = NAMES if filenames is None else filenames
    return util.find_apply([
        lambda: _try_from_dir_file(path, filenames),
        lambda: _try_from_plugin(path) if use_plugins else None,
        lambda: _raise_no_models(path)])

def _try_from_dir_file(path, filenames):
    logging.debug("checking '%s' for model sources", path)
    for name in filenames:
        model_file = os.path.abspath(os.path.join(path, name))
        if os.path.isfile(model_file):
            logging.debug("found model source '%s'", model_file)
            return _load_modelfile(model_file)
    return None

def _try_from_plugin(path):
    data = []
    for name, plugin in guild.plugin.iter_plugins():
        logging.debug(
            "using plugin '%s' to check '%s' for models",
            name, path)
        plugin_models = _plugin_models_for_location(plugin, path)
        for model in plugin_models:
            logging.debug(
                "found model '%s' with plugin '%s'",
                model.get("name"), name)
        data.extend(plugin_models)
    if data:
        return Modelfile(data, os.path.join(path, "__generated__"))
    else:
        return None

def _plugin_models_for_location(plugin, path):
    return list(plugin.models_for_location(path) or [])

def _raise_no_models(path):
    raise NoModels(path)

def from_file(src):
    return _load_modelfile(src)

def _load_modelfile(src):
    return Modelfile(yaml.load(open(src, "r")), src)

def from_file_or_dir(src):
    try:
        return from_file(src)
    except IOError as e:
        if e.errno == errno.EISDIR:
            return from_dir(src)
        raise

def from_string(s, src=None):
    return Modelfile(yaml.load(s), src)
