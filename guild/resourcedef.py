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

"""Facilities for working with resource definitions.

This is in a separate module because resources can show up in
guildfiles and in packages, which are otherwise unrelated.
"""

import collections
import copy
import logging
import operator
import pprint

from guild import util

log = logging.getLogger("guild")


class ResourceFormatError(ValueError):
    pass


class ResourceDefValueError(ValueError):
    pass


class ResourceDef:

    source_types = [
        "config",
        "file",
        "module",
        "url",
    ]
    default_source_type = "file"

    def __init__(self, name, data, fullname=None):
        self.name = name
        self._data = data = _coerce_resdef(data)
        self.fullname = fullname or name
        self.flag_name = data.get("flag-name")
        self.description = data.get("description", "")
        self.preserve_path = data.get("preserve-path")
        self.target_type = data.get("target-type")
        self.default_unpack = data.get("default-unpack", True)
        self.private = bool(data.get("private"))
        self.references = data.get("references", [])
        self.sources = self._init_sources(data.get("sources", []))
        self.target_path = _init_target_path(
            data.get("target-path"),
            data.get("path"),
            f"resource {self.resolving_name}",
        )

    @property
    def resolving_name(self):
        return (
            self.name
            or self.flag_name
            or _joined_resdef_source_desc(self)
            or _unnamed_resource_desc()
        )

    def __repr__(self):
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__} "
            f"'{self.resolving_name}'>"
        )

    def _init_sources(self, data):
        if isinstance(data, list):
            return [self._init_resource_source(src_data) for src_data in data]
        raise ResourceFormatError(
            f"invalid sources value for resource '{self.fullname}': {data!r}"
        )

    def _init_resource_source(self, data):
        if isinstance(data, dict):
            return self._resource_source_for_data(data)
        if isinstance(data, str):
            return self._source_for_type(self.default_source_type, data, {})
        raise ResourceFormatError(
            f"invalid source for resource '{self.fullname}': {data!r}"
        )

    def _resource_source_for_data(self, data):
        data_copy = copy.copy(data)
        type_vals = [data_copy.pop(attr, None) for attr in self.source_types]
        type_items = zip(self.source_types, type_vals)
        type_count = sum((bool(val) for val in type_vals))
        if type_count == 0:
            types_desc = ", ".join(self.source_types)
            raise ResourceFormatError(
                f"invalid source {data} in resource '{self.fullname}': "
                f"missing required attribute (one of {types_desc})"
            )
        if type_count > 1:
            conflicting = ", ".join([item[0] for item in type_items if item[1]])
            raise ResourceFormatError(
                f"invalid source {pprint.pformat(data)} in resource "
                f"'{self.fullname}': conflicting attributes ({conflicting})"
            )
        type_name, type_val = next(item for item in type_items if item[1])
        return self._source_for_type(type_name, type_val, data_copy)

    def _source_for_type(self, type, val, data):
        data = self._coerce_source_data(data)
        if type == "file":
            return ResourceSource(self, f"file:{val}", **data)
        if type == "url":
            return ResourceSource(self, val, **data)
        if type == "module":
            return ResourceSource(self, f"module:{val}", **data)
        if type == "config":
            return ResourceSource(self, f"config:{val}", **data)
        raise AssertionError(type, val, data)

    @staticmethod
    def _coerce_source_data(data):
        return {name.replace("-", "_"): data[name] for name in data}

    @staticmethod
    def _uncoerce_attr_key(key):
        return key.replace("_", "-")


def _coerce_resdef(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"sources": data}
    raise ResourceDefValueError()


def _joined_resdef_source_desc(resdef):
    return ",".join([source.resolving_name for source in resdef.sources])


class ResourceSource:
    def __init__(
        self,
        resdef,
        uri,
        name=None,
        sha256=None,
        unpack=None,
        type=None,
        select=None,
        select_min=None,
        select_max=None,
        warn_if_empty=True,
        optional=False,
        fail_if_empty=False,
        rename=None,
        help=None,
        post_process=None,
        target_path=None,
        target_type=None,
        replace_existing=None,
        always_resolve=None,
        path=None,
        preserve_path=False,
        params=None,
        flag_name=None,
        **kw,
    ):
        self.resdef = resdef
        self.uri = uri
        self._parsed_uri = None
        self.name = name
        self.flag_name = flag_name
        self.sha256 = sha256
        if unpack is not None:
            self.unpack = unpack
        else:
            self.unpack = resdef.default_unpack
        self.type = type
        self.select = _init_resource_source_select(select, select_min, select_max)
        self.optional = optional
        self.warn_if_empty = warn_if_empty
        self.fail_if_empty = fail_if_empty
        self.rename = _init_rename(rename)
        self.post_process = post_process
        self.target_path = _init_target_path(
            target_path,
            path,
            f"source {self.resolving_name}",
        )
        self.target_type = target_type
        self.replace_existing = replace_existing
        self.preserve_path = preserve_path
        self.params = params
        self.always_resolve = always_resolve
        self.help = help
        for key in sorted(kw):
            log.warning(
                "unexpected source attribute '%s' in resource %r",
                self.resdef._uncoerce_attr_key(key),
                self.resolving_name,
            )

    @property
    def parsed_uri(self):
        if self._parsed_uri is None:
            self._parsed_uri = util.parse_url(self.uri)
        return self._parsed_uri

    @property
    def resource_name_part(self):
        return self.name

    def __repr__(self):
        return f"<guild.resourcedef.ResourceSource '{self.resolving_name}'>"

    def __str__(self):
        return self.uri

    @property
    def resolving_name(self):
        return self.name or self.flag_name or self.uri


def _unnamed_resource_desc():
    return "resource"


SelectSpec = collections.namedtuple("SelectSpec", ["pattern", "reduce"])


def _init_resource_source_select(s, s_min, s_max):
    select = []
    select.extend([SelectSpec(x, None) for x in _coerce_list(s, "select")])
    select.extend(
        [SelectSpec(x, _select_reduce_min) for x in _coerce_list(s_min, "select-min")]
    )
    select.extend(
        [SelectSpec(x, _select_reduce_max) for x in _coerce_list(s_max, "select-max")]
    )
    return select


def _select_reduce_min(matches):
    return _select_reduce_op(matches, operator.__lt__)


def _select_reduce_max(matches):
    return _select_reduce_op(matches, operator.__gt__)


def _select_reduce_op(matches, op):
    reduced_val = None
    reduced_m = None
    for m in matches:
        try:
            m_val_str = m.group(1)
        except IndexError:
            pass
        else:
            try:
                m_val = float(m_val_str)
            except ValueError:
                pass
            else:
                if reduced_val is None or op(m_val, reduced_val):
                    reduced_val = m_val
                    reduced_m = m
    if reduced_m:
        assert reduced_val is not None
        return [reduced_m]
    return []


def _init_rename(data):
    if data is None:
        return None
    if not isinstance(data, list):
        data = [data]
    return [_init_rename_spec(item) for item in data]


RenameSpec = collections.namedtuple("RenameSpec", ["pattern", "repl"])


def _init_rename_spec(data):
    if isinstance(data, str):
        pattern, repl = _split_rename_spec(data)
        return RenameSpec(pattern, repl)
    if isinstance(data, dict):
        return RenameSpec(data.get("pattern", ""), data.get("repl", ""))
    raise ResourceFormatError(f"invalid rename spec {data!r}: expected string or map")


def _split_rename_spec(spec):
    parts = util.shlex_split(spec)
    if len(parts) == 2:
        return parts
    if len(parts) == 1:
        return ".*", parts[0]
    raise ResourceFormatError(
        f"invalid rename spec {spec!r}: expected 'PATTERN REPL' or 'NAME'"
    )


def _init_target_path(target_path_arg, path_arg, context):
    """Returns target path for two args.

    The `path` source def attribute is renamed to `target-path` for
    clarity. Maintains backward compatibility for specifying target
    path as `path`.

    Logs a warning if both values are provided and returns the value
    of `target_path_arg`.
    """
    if target_path_arg and path_arg:
        log.warning(
            "target-path and path both specified for %s - using target-path", context
        )
    return target_path_arg or path_arg


def _coerce_list(val, desc):
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return val
    raise ResourceFormatError(f"invalid {desc} val: {val}")
