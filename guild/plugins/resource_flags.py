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

import logging

from guild import guildfile
from guild import op_dep
from guild import plugin as pluginlib

log = logging.getLogger("guild")


class ResourceFlagsPlugin(pluginlib.Plugin):
    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for opdef in m.operations:
                apply_resource_flags(opdef)


def apply_resource_flags(opdef):
    for depdef in opdef.dependencies:
        resdef, _res_location = op_dep.resource_def(depdef, {})
        for source in resdef.sources:
            flagdef = _flagdef_for_source(source, opdef)
            if flagdef:
                _apply_flagdef(flagdef, opdef)


def _flagdef_for_source(source, opdef):
    flag_data = _flag_data_for_source(source)
    if not flag_data:
        return None
    return guildfile.FlagDef(flag_data["name"], flag_data, opdef)


def _flag_data_for_source(source):
    if source.parsed_uri.scheme == "file":
        return _flag_data_for_file(source)
    if source.parsed_uri.scheme == "operation":
        return _flag_data_for_operation(source)
    return None


def _flag_data_for_file(source):
    assert source.parsed_uri.scheme == "file", source.parsed_uri
    if not source.flag_name:
        return None
    return {
        "name": source.flag_name,
        "arg-skip": True,
        "default": source.parsed_uri.path
    }


def _apply_flagdef(flagdef, opdef):
    existing = opdef.get_flagdef(flagdef.name)
    if existing:
        _apply_missing_flagdef_attrs(flagdef, existing)
    else:
        opdef.flags.append(flagdef)


def _flag_data_for_operation(source):
    assert source.parsed_uri.scheme == "operation", source.parsed_uri
    return None


def _apply_missing_flagdef_attrs(flagdef, existing):
    for name in ("arg_skip", "default"):
        existing_val = getattr(existing, name)
        if existing_val is None:
            setattr(existing, name, getattr(flagdef, name))
