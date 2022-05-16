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

import glob
import logging
import os
import re

import six

from guild import file_util
from guild import guildfile
from guild import op_util
from guild import plugin as pluginlib

from . import flags_import_util

log = logging.getLogger("guild")


class _ConfigNotSupported(Exception):
    def __str__(self):
        assert len(self.args) == 1
        return "config type for %s not supported" % self.args[0]


class ConfigFlagsPlugin(pluginlib.Plugin):
    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for opdef in m.operations:
                apply_config_flags(opdef)


def apply_config_flags(opdef):
    config_spec = _config_spec(opdef)
    if not config_spec:
        return
    for src in _iter_config_src(config_spec, opdef):
        _apply_config_src(src, opdef)


class _ConfigSpec:
    def __init__(self, type, val):
        self.type = type
        self.val = val


def _config_spec(opdef):
    if not opdef.flags_dest:
        return None
    if opdef.flags_dest.startswith("config:"):
        return _single_config(opdef.flags_dest[7:])
    if opdef.flags_dest.startswith("multi-config:"):
        return _multi_config(opdef.flags_dest[13:])
    return None


def _single_config(spec):
    return _ConfigSpec("single", spec)


def _multi_config(spec):
    if spec.startswith("!regex!"):
        return _ConfigSpec("regex", spec[7:])
    return _ConfigSpec("glob", spec)


def _iter_config_src(spec, opdef):
    if spec.type == "single":
        yield spec.val
    elif spec.type == "regex":
        for src in _iter_config_regex(spec.val, opdef):
            yield src
    elif spec.type == "glob":
        for src in _iter_config_glob(spec.val, opdef):
            yield src
    else:
        assert False, spec.type


def _opdef_path(src, opdef):
    return os.path.relpath(os.path.join(opdef.guildfile.dir, src))


def _iter_config_regex(pattern, opdef):
    p = re.compile(pattern)
    for src in file_util.find(opdef.guildfile.dir, followlinks=True, includedirs=True):
        if p.match(src):
            yield src


def _iter_config_glob(pattern, opdef):
    gf_dir = opdef.guildfile.dir
    for src in glob.glob(os.path.join(gf_dir, pattern), recursive=True):
        yield os.path.relpath(src, gf_dir)


def _apply_config_src(config_src, opdef):
    flags_import_util.apply_flags(
        opdef,
        import_flags_data_cb=lambda: _flags_data(config_src, opdef),
        apply_flags_data_cb=lambda _data: _ensure_config_dep(config_src, opdef),
    )


def _flags_data(src, opdef):
    data = _load_flags(_opdef_path(src, opdef))
    return {
        name: flags_import_util.flag_data_for_val(val)
        for name, val in data.items()
        if _is_legal_flag_val(val)
    }


def _load_flags(src):
    ext = _flags_src_ext(src)
    if ext in (".yaml", ".yml"):
        return _load_flags_yaml(src)
    elif ext in (".json",):
        return _load_flags_json(src)
    elif ext in (".ini", ".cfg"):
        return _load_flags_cfg(src)
    else:
        raise _ConfigNotSupported(src)


def _flags_src_ext(src):
    ext = os.path.splitext(src)[1].lower()
    if ext == ".in":
        return _flags_src_ext(src[:-3])
    return ext


def _load_flags_yaml(src):
    import yaml

    data = yaml.safe_load(open(src))
    return dict(_iter_keyvals(data))


def _iter_keyvals(data):
    if not isinstance(data, dict):
        return
    for basename, val in data.items():
        if isinstance(val, dict):
            for name, val in _iter_keyvals(val):
                yield ".".join([basename, name]), val
        else:
            yield basename, val


def _load_flags_json(src):
    import json

    data = json.load(open(src))
    return dict(_iter_keyvals(data))


def _load_flags_cfg(src):
    import configparser

    config = configparser.ConfigParser()
    config.read(src)
    data = {
        name: _read_typed_cfg(config, "DEFAULT", name) for name in config.defaults()
    }
    for section in config.sections():
        for name in config.options(section):
            val = _read_typed_cfg(config, section, name)
            data["%s.%s" % (section, name)] = val
    return data


def _read_typed_cfg(cfg, section, name):
    try:
        return cfg.getint(section, name)
    except ValueError:
        try:
            return cfg.getfloat(section, name)
        except ValueError:
            try:
                return cfg.getboolean(section, name)
            except ValueError:
                return cfg.get(section, name)


def _is_legal_flag_val(val):
    return val is None or isinstance(val, (six.string_types, int, float, bool, list))


def _ensure_config_dep(config_src, opdef):
    if not _has_config_dep(opdef, config_src):
        depdef = guildfile.OpDependencyDef(
            {
                "config": config_src,
                "replace-existing": True,
            },
            opdef,
        )
        opdef.dependencies.append(depdef)


def _has_config_dep(opdef, config_src):
    config_source_uri = "config:%s" % config_src
    for resdef in op_util.iter_opdef_resources(opdef):
        for source in resdef.sources:
            if source.uri == config_source_uri:
                return True
    return False
