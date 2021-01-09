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

import logging
import os

import six

from guild import guildfile
from guild import op_util
from guild import plugin as pluginlib

from . import flags_import_util

log = logging.getLogger("guild")


class _ConfigNotSupported(Exception):
    pass


class ConfigFlagsPlugin(pluginlib.Plugin):
    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for opdef in m.operations:
                _maybe_apply_flags(opdef)


def _maybe_apply_flags(opdef):
    config_src = _config_src(opdef)
    if not config_src:
        return
    flags_import_util.apply_flags(
        opdef,
        lambda: _flags_data(config_src),
        lambda _data: _ensure_config_dep(config_src, opdef),
    )


def _config_src(opdef):
    if opdef.flags_dest and opdef.flags_dest.startswith("config:"):
        return opdef.flags_dest[7:]
    return None


def _flags_data(src):
    data = _load_flags(src)
    return {
        name: flags_import_util.flag_data_for_val(val)
        for name, val in data.items()
        if _is_legal_flag_val(val)
    }


def _load_flags(src):
    ext = os.path.splitext(src)[1].lower()
    if ext in (".yaml", ".yml"):
        return _load_flags_yaml(src)
    elif ext in (".json",):
        return _load_flags_json(src)
    elif ext in (".ini", ".cfg"):
        return _load_flags_cfg(src)
    else:
        raise _ConfigNotSupported(src)


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
        depdef = guildfile.OpDependencyDef({"config": config_src}, opdef)
        opdef.dependencies.append(depdef)


def _has_config_dep(opdef, config_src):
    config_source_uri = "config:%s" % config_src
    for resdef in op_util.iter_opdef_resources(opdef):
        for source in resdef.sources:
            if source.uri == config_source_uri:
                return True
    return False
