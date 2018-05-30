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

from guild import workflow as wf

from guild.workflow import file_node
from guild.workflow import url_node

class ResourceNode(wf.Node):

    def __init__(self, resource):
        self.resource = resource

    def get_description(self):
        return "Resource '{}'".format(self.resource.resdef.name)

    def get_deps(self):
        return [
            _node_for_source(source, self.resource)
            for source in self.resource.resdef.sources
        ]

    def run(self):
        pass

def _node_for_source(source, resource):
    uri_scheme = source.parsed_uri.scheme
    if uri_scheme == "file":
        return file_node.FileNode(source, resource)
    elif uri_scheme in ("http", "https"):
        return url_node.URLNode(source, resource)

    else:
        raise AssertionError(source)
