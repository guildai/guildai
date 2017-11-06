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

"""Facilities for working with resource definitions.

This is in a separate module because resources can show up in
modelfiles and in packages, which are otherwise unrelated.
"""

from __future__ import absolute_import
from __future__ import division

import logging

from guild import resolve
from guild import util

log = logging.getLogger("core")

class ResourceFormatError(ValueError):
    pass

class ResourceDef(object):

    source_types = ["file", "url"]

    def __init__(self, name, data):
        self.name = name
        self.fullname = name
        self.description = data.get("description", "")
        self.path = data.get("path")
        self.sources = self._init_sources(data.get("sources", []))
        self.private = bool(data.get("private"))

    @staticmethod
    def get_source_resolver(source):
        scheme = source.parsed_uri.scheme
        if scheme == "file":
            return resolve.FileResolver(source)
        elif scheme in ["http", "https"]:
            return resolve.URLResolver(source)
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
                "invalid sources for resource '%s'"
                % self.fullname)

    def _init_resource_source(self, data):
        if isinstance(data, dict):
            type_vals = [data.pop(attr, None) for attr in self.source_types]
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
                    % (data, self.fullname, conflicting))
            type_name, type_val = next(
                item for item in type_items if item[1]
            )
            return self._source_for_type(type_name, type_val, data)
        elif isinstance(data, str):
            return self._source_for_type("file", data, {})
        else:
            raise ResourceFormatError(
                "invalid source for resource '%s': %s"
                % (self.fullname, data))

    def _source_for_type(self, type, val, data):
        if type == "file":
            return ResourceSource(self, "file:%s" % val, **data)
        elif type == "url":
            return ResourceSource(self, val, **data)
        else:
            raise AssertionError(type, val, data)

class ResourceSource(object):

    def __init__(self, resdef, uri, sha256=None, unpack=True,
                 type=None, extract=None, **kw):
        self.resdef = resdef
        self.uri = uri
        self._parsed_uri = None
        self.sha256 = sha256
        self.unpack = unpack
        self.type = type
        self.extract = extract
        for key in kw:
            log.warning(
                "unexpected source attribute '%s' in resource '%s'",
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
