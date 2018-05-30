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

    user_detail_level = wf.MEDIUM

    def __init__(self, resource, op_node):
        self.resource = resource
        self.op_node = op_node

    def get_description(self):
        return "Resolve resource '{}'".format(self.resource.resdef.name)

    def deps(self):
        return [
            _node_for_source(source, self)
            for source in self.resource.resdef.sources
        ]

    def run(self):
        pass

def _node_for_source(source, resource_node):
    uri_scheme = source.parsed_uri.scheme
    if uri_scheme == "file":
        return file_node.FileNode(source, resource_node)
    elif uri_scheme in ("http", "https"):
        return url_node.URLNode(source, resource_node)

    else:
        raise AssertionError(source)
