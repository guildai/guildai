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

def from_data(data, res_context):
    data = data or {}
    return {
        name: ResourceDef(name, data[name], res_context)
        for name in data
    }

class ResourceDef(object):

    def __init__(self, name, data, res_context):
        self.name = name
        self.description = data.get("description", "")
        self.sources = [
            ResourceSource(src_data, name, res_context)
            for src_data in data.get("sources", [])]

class ResourceSource(object):

    def __init__(self, data, res_name, res_context):
        urls = data.get("urls", [])
        url = data.get("url")
        if url and urls:
            logging.warning(
                "cannot use both 'url' and 'urls' in a resource "
                "source (resource '%s' in %s)", res_name, res_context)
        self.urls = [url] if url else self.urls
        self.sha256 = data.get("sha256")
        self.unpack = bool(data.get("unpack"))
