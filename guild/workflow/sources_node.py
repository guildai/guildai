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

class SourcesNode(wf.Node):

    user_detail_level = wf.MEDIUM

    def __init__(self, resdef, op_node):
        self.resdef = resdef
        self.op_node = op_node

    def get_description(self):
        return "Resolve source '{}'".format(self.source.parsed_uri.path)

    def deps(self):
        for x in []:
            yield x

    def run(self):
        pass
