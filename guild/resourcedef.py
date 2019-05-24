# Copyright 2017-2019 TensorHub, Inc.
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

from __future__ import absolute_import
from __future__ import division

import collections
import copy
import logging
import operator
import pprint

import six

from guild import resolver
from guild import util

log = logging.getLogger("guild")

class ResourceFormatError(ValueError):
    pass

class ResourceDef(object):

    source_types = ["file", "url", "module"]
    default_source_type = "file"

    def __init__(self, name, data, fullname=None):
        self.name = name
        self.data = data
        self.fullname = fullname or name
        self.description = data.get("description", "")
        self.path = data.get("path")
        self.default_unpack = data.get("default-unpack", True)
        self.private = bool(data.get("private"))
        self.references = data.get("references", [])
        self.sources = self._init_sources(data.get("sources", []))

    def get_source_resolver(self, source, resource):
        scheme = source.parsed_uri.scheme
        cls = self._resolver_class_for_scheme(scheme)
        if cls:
            return cls(source, resource)
        return None

    @staticmethod
    def _resolver_class_for_scheme(scheme):
        if scheme == "file":
            return resolver.FileResolver
        elif scheme in ["http", "https"]:
            return resolver.URLResolver
        elif scheme == "module":
            return resolver.ModuleResolver
        else:
            return None

    def __repr__(self):
        return ("<%s.%s '%s'>" % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.name))

    def _init_sources(self, data):
        if isinstance(data, list):
            return [self._init_resource_source(src_data) for src_data in data]
        else:
            raise ResourceFormatError(
                "invalid sources value for resource '%s': %r"
                % (self.fullname, data))

    def _init_resource_source(self, data):
        if isinstance(data, dict):
            data_copy = copy.copy(data)
            type_vals = [
                data_copy.pop(attr, None)
                for attr in self.source_types
            ]
            type_items = zip(self.source_types, type_vals)
            type_count = sum([bool(val) for val in type_vals])
            if type_count == 0:
                raise ResourceFormatError(
                    "invalid source %s in resource '%s': missing required "
                    "attribute (one of %s)"
                    % (data, self.fullname, ", ".join(self.source_types)))
            elif type_count > 1:
                conflicting = ", ".join([
                    item[0] for item in type_items if item[1]
                ])
                raise ResourceFormatError(
                    "invalid source %s in resource '%s': conflicting "
                    "attributes (%s)"
                    % (pprint.pformat(data), self.fullname, conflicting))
            type_name, type_val = next(
                item for item in type_items if item[1]
            )
            return self._source_for_type(type_name, type_val, data_copy)
        elif isinstance(data, str):
            return self._source_for_type(self.default_source_type, data, {})
        else:
            raise ResourceFormatError(
                "invalid source for resource '%s': %s"
                % (self.fullname, data))

    def _source_for_type(self, type, val, data):
        data = self._coerce_source_data(data)
        if type == "file":
            return ResourceSource(self, "file:%s" % val, **data)
        elif type == "url":
            return ResourceSource(self, val, **data)
        elif type == "module":
            return ResourceSource(self, "module:%s" % val, **data)
        else:
            raise AssertionError(type, val, data)

    @staticmethod
    def _coerce_source_data(data):
        return {
            name.replace("-", "_"): data[name]
            for name in data
        }

class ResourceSource(object):

    def __init__(self, resdef, uri, name=None, sha256=None, unpack=None,
                 type=None, select=None, select_min=None, select_max=None,
                 rename=None, help=None, post_process=None, path=None, **kw):
        self.resdef = resdef
        self.uri = uri
        self._parsed_uri = None
        self.name = name or uri
        self.sha256 = sha256
        if unpack is not None:
            self.unpack = unpack
        else:
            self.unpack = resdef.default_unpack
        self.type = type
        self.select = _init_resource_source_select(
             select, select_min, select_max)
        self.rename = _init_rename(rename)
        self.post_process = post_process
        self.path = path
        self.help = help
        for key in kw:
            log.warning(
                "unexpected source attribute '%s' in resource %r",
                key, resdef.fullname)

    @property
    def parsed_uri(self):
        if self._parsed_uri is None:
            self._parsed_uri = util.parse_url(self.uri)
        return self._parsed_uri

    def __repr__(self):
        return "<guild.resourcedef.ResourceSource '%s'>" % self.uri

    def __str__(self):
        return self.uri

SelectSpec = collections.namedtuple(
    "SelectSpec", [
        "pattern",
        "reduce",
    ])

def _init_resource_source_select(s, s_min, s_max):
    select = []
    select.extend([
        SelectSpec(x, None)
        for x in _coerce_list(s, "select")])
    select.extend([
        SelectSpec(x, _select_reduce_min)
        for x in _coerce_list(s_min, "select-min")])
    select.extend([
        SelectSpec(x, _select_reduce_max)
        for x in _coerce_list(s_max, "select-max")])
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

RenameSpec = collections.namedtuple(
    "RenameSpec", [
        "pattern",
        "repl",
    ])

def _init_rename_spec(data):
    if isinstance(data, six.string_types):
        pattern, repl = _split_rename_spec(data)
        return RenameSpec(pattern, repl)
    elif isinstance(data, dict):
        return RenameSpec(
            data.get("pattern", ""),
            data.get("repl", ""))
    else:
        raise ResourceFormatError(
            "invalid rename spec %r: expected string or map"
            % data)

def _split_rename_spec(spec):
    parts = util.shlex_split(spec)
    if len(parts) != 2:
        raise ResourceFormatError(
            "invalid rename spec %r: expected 'PATTERN REPL'"
            % spec)
    return parts

def _coerce_list(val, desc):
    if val is None:
        return []
    elif isinstance(val, six.string_types):
        return [val]
    elif isinstance(val, list):
        return val
    else:
        raise ResourceFormatError("invalid %s val: %s" % (desc, val))
